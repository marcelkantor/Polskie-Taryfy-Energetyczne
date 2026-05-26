# Polskie Taryfy Energetyczne

Integracja Home Assistant do prostego monitorowania polskich taryf energetycznych na potrzeby automatyzacji EMS.

## Instalacja przez HACS

1. Dodaj to repozytorium jako custom repository typu `Integration`.
2. Zainstaluj integracje `Polskie Taryfy Energetyczne`.
3. Uruchom ponownie Home Assistant.
4. Dodaj integracje z poziomu `Ustawienia -> Urzadzenia i uslugi`.

## Funkcje

- ceny brutto `PLN/kWh` bez rozbijania rachunku na dystrybucje, VAT i oplaty stale,
- presety 2026 z `cena-pradu.pl`,
- G11 wedlug operatora: ENEA, ENERGA, PGE, E.ON, TAURON,
- G12 i G12w jako srednie ceny dla Polski,
- wlasne ceny brutto dla strefy wysokiej/jednostrefowej i niskiej,
- encje EMS: aktualna strefa cenowa, niska strefa, czas do zmiany strefy i cena ponizej sredniej prognozy.

## Zrodla presetow

- G11: http://cena-pradu.pl/tabela.html
- G12 i G12w: http://cena-pradu.pl/taryfy.html

Presety sa zapisane lokalnie w integracji, w pliku `custom_components/polskie_taryfy_energetyczne/data/presets_2026.json`. Integracja nie scrapuje strony przy starcie Home Assistant.

## Zmiana taryfy i cen

Po instalacji przejdz do `Ustawienia -> Urzadzenia i uslugi -> Polskie Taryfy Energetyczne -> Konfiguruj`.

W opcjach integracji mozna zmienic zrodlo cen, taryfe, operatora dla presetow G11, sensor zuzycia energii oraz wlasne ceny brutto. Po zapisaniu Home Assistant przeladuje wpis integracji i sensory zaczna uzywac nowych wartosci.

Integracja opisuje ceny przez strefy cenowe, a nie przez pore dnia. Dla taryf wielostrefowych uzywane sa strefy `low` i `high`, poniewaz tanie okna moga wystepowac takze w ciagu dnia. Dla taryfy jednostrefowej uzywana jest strefa `single`.
