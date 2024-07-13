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
from pypdf import PdfReader

# https://regex101.com/
regex_str_azonosito = '.*megadott adatokkal a\(z\) ([0-9]+) azonosító számon.*'
regex_str_meroazonosito_meroallas_email = '.*[^0-9]*([0-9]+) - ([0-9]+) kWh Hatásos 24h \/kWh.*'
regex_str_meroazonosito_meroallas_pdf = 'Leolvasás oka[ ]+([0-9]+).+Hatásos 24h \/kWh.+[0-9]+.+[0-9]{4}.[0-9]{2}.[0-9]{2}[^0-9]+([0-9]+)[^0-9]+[0-9]{4}.[0-9]{2}.[0-9]{2}.+Normál.+rögzítés.+Leolvasás dátuma: ([0-9]{4}.[0-9]{2}.[0-9]{2})'

def parse(f):
    leolvasasdatumaPdf = None
    mail = mailparser.parse_from_file_obj(f)
    #print(mail.date)
    #print(mail.from_)
    #print(mail.delivered_to)
    #print(mail.to)
    #print(mail.body)
    mailTimestamp = int(time.mktime(mail.date.timetuple()))
    body = mail.body #.replace('\n', '')

    rd = re.search(regex_str_azonosito, body)
    if rd is None:
        raise Exception('Nincs regexp match az emailben a rögzítés azonosító számára')

    if len(rd.groups()) != 1:
        raise Exception('Nem találom a rögzítés azonosító számát!')

    azonosito = rd.group(1)

    rd = re.search(regex_str_meroazonosito_meroallas_email, body)
    if rd is None:
        # Nincs match, muszáj megnézzem van e pdf csatolmány hogy meglegyen a mérő száma és aktuális állása
        #sys.stderr.write("Emailben nem találom a mérő azonosító számát és a mérőállást. Megnézem hátha van csatolmány.\n")
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

    else:
        if len(rd.groups()) != 2:
            sys.stderr.write('Nem találom a mérő azonosító számát és a mérőállást!')
            exit(1)
        # Minden benne van közvetlenül az emailben amit keresek
        meroszam = rd.group(1)
        meroallas = rd.group(2)

    if len(azonosito) == 0:
        raise Exception("Hibás mező érték: azonosito")

    if len(meroszam) == 0:
        raise Exception("Hibás mező érték: meroszam")

    if len(meroallas) == 0:
        raise Exception("Hibás mező érték: meroallas")

    if leolvasasdatumaPdf != None:
        if abs(leolvasasdatumaPdf - mailTimestamp) > 24 * 60 * 60:   # 24 hour
            sys.stderr.write("FIGYELMEZTETÉS! Az emailből jövő időpont jelentősen eltér a pdf-ben lévő dátumtól!\n")

    return {
        'emailTime' : mailTimestamp,
        'azonosito' : int(azonosito),
        'meroszam' : int(meroszam),
        'meroallas' : int(meroallas),
        'leolvasasdatumaPdf' : leolvasasdatumaPdf,
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

    leolvasasdatumaTs = int(time.mktime(datetime.datetime.strptime(leolvasasdatuma,"%Y.%m.%d").timetuple()))

    return meroszam,meroallas,leolvasasdatumaTs

data = fromFile()
print(json.dumps(data))
