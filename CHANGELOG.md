# Changelog

## 0.3.3

- Dodano dodatkowe odświeżenie koordynatora zaplanowane na najbliższą granicę strefy cenowej.
- Poprawiono precyzję przełączania stref cenowych dla automatyzacji EMS.

## 0.3.2

- Zaokrąglono sensory cen brutto oraz atrybuty prognozy cen do dwóch miejsc po przecinku.
- Dodano sugerowaną precyzję wyświetlania dla sensorów cen i czasu do zmiany strefy.

## 0.3.1

- Podzielono konfigurację na dwa kroki, aby pola własnych cen brutto były widoczne tylko
  po wybraniu własnego źródła cen.
- Zaktualizowano polskie etykiety i opisy konfiguracji.

## 0.3.0

- Przebudowano model cen wokół cen brutto w `PLN/kWh`.
- Dodano wbudowane presety na 2026 rok na podstawie danych z `cena-pradu.pl`.
- Dodano presety G11 dla poszczególnych operatorów oraz uśrednione presety G12/G12w.
- Usunięto z integracji pola stawek dystrybucyjnych, opłaty stałej miesięcznej i VAT.
- Zmieniono klasę IoT integracji na `local_polling`, ponieważ presety są dostarczane lokalnie.

## 0.2.2

- Usunięto tymczasowe fallbacki zgodności dla `zone_1_rate` i `night_rate`
  na etapie testów.

## 0.2.1

- Poprawiono niespójne etykiety w przepływie opcji, zastępując pozostałe starsze
  pole formularza `zone_1_rate` polem `high_rate`.

## 0.2.0

- Zastąpiono nazewnictwo dzień/noc terminologią wysokiej i niskiej strefy cenowej.
- Dodano sensory przydatne dla EMS: aktualna strefa cenowa, następna zmiana strefy,
  czas do zmiany strefy oraz średnia cena z prognozy.
- Dodano sensory binarne dla niskiej strefy cenowej oraz ceny poniżej średniej z prognozy.

## 0.1.1

- Dodano przepływ opcji do zmiany taryfy i stawek po instalacji.
- Dodano zasoby marki dla HACS.
- Zaktualizowano metadane repozytorium i workflow walidacji.
- Poprawiono linki w manifeście oraz metadane właściciela kodu.

## 0.1.0

- Początkowy szkielet niestandardowej integracji Home Assistant.
- Dodano strukturę HACS, config flow, koordynator i przykładowe sensory.
