#!/usr/bin/python
import os
import re
import sys
import mailparser   # https://pypi.org/project/mail-parser/
import json
import base64
import tempfile
import time
import datetime
from dateutil import tz
from datetime import datetime
from pypdf import PdfReader

# https://regex101.com/
regex_str_azonosito = r'.*megadott adatokkal a\(z\) ([0-9]+) azonosító számon.*'
regex_str_meroazonosito_meroallas_elmuemasz_email = r'.*[^0-9]*([0-9]+) - ([0-9]+) kWh Hatásos 24h \/kWh.*'
regex_str_meroazonosito_meroallas_pdf = r'Leolvasás oka[ ]+([0-9]+).+Hatásos 24h \/kWh.+[0-9]+.+[0-9]{4}.[0-9]{2}.[0-9]{2}[^0-9]+([0-9]+)[^0-9]+[0-9]{4}.[0-9]{2}.[0-9]{2}.+Normál.+rögzítés.+Leolvasás dátuma: ([0-9]{4}.[0-9]{2}.[0-9]{2})'
regex_str_meroazonosito_meroallas_eon_email = r'Gyáriszám.+Mérőállás[^0-9]+([0-9]+)[^0-9]+([0-9]+)[^0-9]+Köszönjük'
regex_str_meroazonosito_meroallas_datumido_mvmnext_email = r'Gyári szám 	Diktált érték\n([0-9]+)[^\d]+(.*) kWh\n\nDiktálás időpontja: (.*)\n'

def eonMeroallasMeroszam(body):
    rd = re.search(regex_str_meroazonosito_meroallas_eon_email, body)
    if rd is None:
        raise Exception("EON levél? Nem találom a mérőszámot és a mérőállást benne!")

    if len(rd.groups()) != 2:
        raise Exception("Nem az elvárt szamú regex groupot kaptam! Ellenőrizd a regexpet!")

    meroszam = rd.group(1)
    meroallas = rd.group(2)

    return meroszam, meroallas

def elmuemaszMeroallasMeroszam(body):
    rd = re.search(regex_str_meroazonosito_meroallas_elmuemasz_email, body)
    if rd is None:
        raise Exception("ELMU-EMASZ levél? Nem találom a mérőszámot és a mérőállást benne!")

    if len(rd.groups()) != 2:
        raise Exception("Nem az elvart szamu regex groupot kaptam! Ellenorizd a regexpet!")

    meroszam = rd.group(1)
    meroallas = rd.group(2)

    return meroszam, meroallas

def mvmnextMeroallasMeroszamDatumido(body):
    rd = re.search(regex_str_meroazonosito_meroallas_datumido_mvmnext_email, body)
    if rd is None:
        raise Exception("MVM Next levél? Nem találom a mérőszámot, a mérőállást és a leolvasás idejét benne!")

    if len(rd.groups()) != 3:
        raise Exception("Nem az elvart szamu regex groupot kaptam! Ellenorizd a regexpet!")

    meroszam = rd.group(1)
    # drop all non digit characters to be a valid string represented number
    meroallas = ""
    for c in rd.group(2):
        if c.isdigit():
            meroallas = meroallas + c

    leolvasasido = rd.group(3)
    t = datetime.strptime(leolvasasido,"%Y.%m.%d. %H:%M")
    leolvasasidoTs = int(t.timestamp())

    return meroszam, meroallas, leolvasasidoTs


def elmuemaszCsatolmany(mail):
    meroszam = ""
    meroallas = ""
    leolvasasdatumaPdf = ""

    # Nincs match, muszáj megnézzem van e pdf csatolmány hogy meglegyen a mérő száma és aktuális állása
    #sys.stderr.write("Emailben nem találom a mérő azonosító számát és a mérőállást. Megnézem hátha van csatolmány.\n")
    if len(mail.attachments) == 0:
        raise Exception("Nincs csatolt fájl!")

    for attachement in mail.attachments:
        # binary, mail_content_type, payload, filename, content_transfer_encoding, content-id
        if attachement["mail_content_type"] == "application/pdf":
            if attachement["filename"].lower()[-4:] == ".pdf":
                attachement_data = bytearray(base64.b64decode(attachement["payload"]))
                temp_file_name = tempfile.mktemp()
                f = open(temp_file_name, "wb")
                f.write(attachement_data)
                f.close()
                try:
                    meroszam,meroallas,leolvasasdatumaPdf = parsePdf(temp_file_name)
                except Exception as e:
                    raise e
                finally:
                    os.unlink(temp_file_name)

    return meroszam,meroallas,leolvasasdatumaPdf

def rogzitesAzonosito(body):
    # rögzítés azonosító
    rd = re.search(regex_str_azonosito, body)
    if rd is None:
        raise Exception('Nincs regexp match az emailben a rögzítés azonosító számára')

    if len(rd.groups()) != 1:
        raise Exception('Nem találom a rögzítés azonosító számát!')

    azonosito = rd.group(1)
    return azonosito

def parse(f):
    leolvasasdatumaContent = None
    meroszam = ""
    meroallas = ""
    azonosito = ""

    mail = mailparser.parse_from_file_obj(f)
    #print(mail.date)
    #print(mail.from_)
    #print(mail.delivered_to)
    #print(mail.to)
    #print(mail.body)
    mailTimestamp = int(mail.date.timestamp())
    body = mail.body #.replace('\n', '')

    try:
        # A legtobb email ebben a formátumban van
        meroszam, meroallas = elmuemaszMeroallasMeroszam(body)
        try:
            azonosito = rogzitesAzonosito(body)
        except Exception as e:
            sys.stderr.write("ERROR! Nem találom a diktálás azonosítót! %s\n" %e)
    except Exception as e:
        #sys.stderr.write("%s\n" %e)
        try:
            # Néhány levél érkezett úgy, hogy pdf csatolmány volt hozzá
            meroszam, meroallas, leolvasasdatumaContent = elmuemaszCsatolmany(mail)
            try:
                azonosito = rogzitesAzonosito(body)
            except Exception as e:
                sys.stderr.write("ERROR! Nem találom a diktálás azonosítót! %s\n" %e)
        except Exception as e:
            #sys.stderr.write("%s\n" %e)
            try:
                # Az éves fényképes Android appos leolvasásoknál meg ilyen email jön.
                # Ebben a formátumban nincs diktálás azonosító szám megadva.
                meroszam, meroallas = eonMeroallasMeroszam(body)
                azonosito = "0"
            except Exception as e:
                #sys.stderr.write("%s\n" %e)
                try:
                    # Az éves fényképes Android appos leolvasásoknál meg ilyen email jön.
                    # Ebben a formátumban nincs diktálás azonosító szám megadva.
                    meroszam, meroallas, leolvasasdatumaContent = mvmnextMeroallasMeroszamDatumido(body)
                    azonosito = "0"
                except Exception as e:
                    sys.stderr.write("ERROR! Sehogyse sikerult parsolni a fájlt!\n" %e)

    if len(azonosito) == 0:
        raise Exception("Hibás mező érték: azonosito")

    if len(meroszam) == 0:
        raise Exception("Hibás mező érték: meroszam")

    if len(meroallas) == 0:
        raise Exception("Hibás mező érték: meroallas")

    if leolvasasdatumaContent != None:
        if abs(leolvasasdatumaContent - mailTimestamp) > 24 * 60 * 60:   # 24 hour
            sys.stderr.write("FIGYELMEZTETÉS! Az emailből jövő időpont jelentősen eltér a pdf-ben lévő dátumtól!\n")

    return {
        'emailTime' : mailTimestamp,
        'azonosito' : int(azonosito),
        'meroszam' : int(meroszam),
        'meroallas' : int(meroallas),
        'leolvasasdatumaContent' : leolvasasdatumaContent,
    }

def fromFile():
    if len(sys.argv) != 2:
        sys.stderr.write("Pontosan egy paramétert kérek!\n")
        exit(1)

    filename = sys.argv[1]

    if len(filename) == 0:
        sys.stderr.write("Nulla hosszú paraméter!\n")
        exit(1)

    try:
        with open(filename, 'r') as f:
            return parse(f)
    except Exception as e:
        sys.stderr.write("%s\n" % e)
        exit(1)

def parsePdf(fileName):
    reader = PdfReader(fileName)
    pdfText = ""
    for page in reader.pages:
        pdfText += page.extract_text() + "\n"

    pdfText = pdfText.replace('\n', '')

    rd = re.search(regex_str_meroazonosito_meroallas_pdf, pdfText)
    if rd is None:
        raise Exception('Nincs regexp match a pdf-ben a mérő számra és a mérő állásra! %s' % pdfText)

    if len(rd.groups()) != 3:
        raise Exception('Nem találom a mérő számát, az aktuális állását és a leolvasás dátumát! %s' % pdfText)

    meroszam = rd.group(1)
    meroallas = rd.group(2)
    leolvasasdatuma = rd.group(3)

    leolvasasdatumaTs = int(datetime.strptime(leolvasasdatuma,"%Y.%m.%d").timestamp())

    return meroszam,meroallas,leolvasasdatumaTs

data = fromFile()
print(json.dumps(data))
