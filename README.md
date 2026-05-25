# Polskie Taryfy Energetyczne

Integracja Home Assistant do monitorowania polskich taryf energetycznych, stawek wlasnych oraz prognoz cenowych.

## Instalacja przez HACS

1. Dodaj to repozytorium jako custom repository typu `Integration`.
2. Zainstaluj integracje `Polskie Taryfy Energetyczne`.
3. Uruchom ponownie Home Assistant.
4. Dodaj integracje z poziomu `Ustawienia -> Urzadzenia i uslugi`.

## Funkcje

- wybor operatora i taryfy: `G11`, `G12`, `G12w`,
- wlasne stawki energii dziennej, nocnej/weekendowej, dystrybucji i oplat stalych,
- `DataUpdateCoordinator` przygotowany pod pobieranie cen i prognoz z API,
- sensory ceny bieżącej, szacowanego kosztu godzinowego oraz prognoz cenowych.

## Status

To jest szkielet integracji. Modul `api.py` zawiera przykladowego klienta z fallbackiem na stawki wpisane przez uzytkownika.

