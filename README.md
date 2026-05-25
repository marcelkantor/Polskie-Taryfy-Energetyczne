# Polskie Taryfy Energetyczne

Integracja Home Assistant do monitorowania polskich taryf energetycznych, stawek wlasnych oraz prognoz cenowych.

## Instalacja przez HACS

1. Dodaj to repozytorium jako custom repository typu `Integration`.
2. Zainstaluj integracje `Polskie Taryfy Energetyczne`.
3. Uruchom ponownie Home Assistant.
4. Dodaj integracje z poziomu `Ustawienia -> Urzadzenia i uslugi`.

## Funkcje

- wybor operatora i taryfy: `G11`, `G12`, `G12w`,
- wlasne stawki wysokiej/jednostrefowej i niskiej strefy cenowej,
- encje EMS: aktualna strefa cenowa, niska strefa, czas do zmiany strefy i cena ponizej sredniej prognozy,
- `DataUpdateCoordinator` przygotowany pod pobieranie cen i prognoz z API,
- sensory ceny bieżącej, szacowanego kosztu godzinowego oraz prognoz cenowych.

## Zmiana taryfy i stawek

Po instalacji przejdz do `Ustawienia -> Urzadzenia i uslugi -> Polskie Taryfy Energetyczne -> Konfiguruj`.

W opcjach integracji mozna zmienic operatora, taryfe, sensor zuzycia energii oraz wszystkie stawki. Po zapisaniu Home Assistant przeladuje wpis integracji i sensory zaczna uzywac nowych wartosci.

Integracja opisuje ceny przez strefy cenowe, a nie przez pore dnia. Dla taryf wielostrefowych uzywane sa strefy `low` i `high`, poniewaz tanie okna moga wystepowac takze w ciagu dnia. Dla taryfy jednostrefowej uzywana jest strefa `single`.

## Status

To jest szkielet integracji. Modul `api.py` zawiera przykladowego klienta z fallbackiem na stawki wpisane przez uzytkownika.
