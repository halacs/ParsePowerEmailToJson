A script célja, hogy a havi villanyóra állás diktálás után kapott MVM Next emaileket json formába konvertálja ezzel lehetővé téve a további feldolgozást.

Az emaileket kimentheted egyesével fájlba kézzel, vagy használhatod a Thunderbird FiltaQuilla addonját ami egyből ezt a scriptet is meg tudja hívni.

A script kimenetét példul `mosquitto_pub` paranccsal lehet MQTT-be küldeni.

# Minta futás 1

## Bemenet:

```text
Tisztelt Ügyfelünk!

Az Ön által megadott adatokkal a(z) 012345678901 azonosító számon a kért
mérőállásokat rögzítettük.

9876543210 - 5089 kWh Hatásos 24h /kWh 

Üdvözlettel,
MVM Next Energiakereskedelmi Zrt.
```

## Kimenet

```text
{"emailTime": 1711962050, "azonosito": 012345678901, "meroszam": 9876543210, "meroallas": 5089, "leolvasasdatumaPdf": ""}
```

# Minta futás 2

## Bemenet
2020. december előtti emailekben még más formátumot alkalmazott a szolgáltató: a villanyóra azonosítója és aktuális állása egy csatolt pdf fájlban volt megtalálható. A program ezt a formátumot is képes kezelni.

```text


Tisztelt Ügyfelünk!

Az Ön által megadott adatokkal a(z) 012345678901 azonosító számon a kért
mérőállásokat rögzítettük.

Amennyiben jelen levelünk csatolt mellékletet nem tartalmaz, úgy azt
megtekintheti az elintézett műveletek menüpont alatt.


Üdvözlettel,
ELMŰ-ÉMÁSZ Ügyfélszolgálat
```

## Kimenet
```text
{"emailTime": 1475687521, "azonosito": 012345678901, "meroszam": 9876543210, "meroallas": 80333, "leolvasasdatumaPdf": 1475618400}
```

# Minta futás 3

## Bemenet:

```text
Tisztelt Ügyfelünk!
Fényképes mérőállás bejelentését társaságunk fogadta.
A beküldött fénykép és mérőállás feldolgozását megkezdtük.
Sikeres feldolgozást követően jelenik meg a mérőállások listáján. Kérjük
szíves türelmét!
A következő mérőállás(ok) kerültek be a rendszerünkbe:

Gyáriszám       Mérőállás

9876543210               1457
Köszönjük mérőállás bejelentését!

Üdvözlettel:

E.ON Ügyfélszolgálati Kft.
```

## Kimenet

```text
{"emailTime": 1711962050, "azonosito": 0, "meroszam": 9876543210, "meroallas": 1457, "leolvasasdatumaPdf": ""}
```

# Minta futás 3
MVM Next összevont 2024 augusztustól.

A HTML levélhez van plain text is így azt parsoljuk.

## Bemenet:

```text
Kedves X Y!

Sikeres diktálását az alábbi adatokkal rögzítettük:


Gyári szám 	Diktált érték
9876543210 	1457 kWh

Diktálás időpontja: 2024.08.01. 09:10

Gázmérőt diktált? Ha két éves leolvasás között egymás után kétszer, vagy 
összesen háromszor nem, vagy nem időben diktálja be gázmérője állását, a 
következő éves leolvasás után automatikusan átállítjuk hőmérsékletfüggő 
részszámlázásra.

 


A jelenlegi ügyintézéssel kapcsolatban szeretnénk megismerni a véleményét. 
Kérjük, kattintson az alábbi linkre:
Ügyfélelégedettség-mérés
...
```

## Kimenet

```text
{"emailTime": 1711962050, "azonosito": 0, "meroszam": 9876543210, "meroallas": 1457, "leolvasasdatumaPdf": ""}
```
