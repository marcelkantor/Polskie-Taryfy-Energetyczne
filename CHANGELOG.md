# Changelog

## 0.3.7

- Dodano opcjonalny sensor ceny energii czynnej/RCE dla taryfy `G14dynamic`.
- Dodano sensor pełnej ceny zakupu brutto wyliczany jako cena energii czynnej/RCE plus stawka dystrybucji G14dynamic.
- Zmieniono nazwę sensora bieżącej ceny na neutralną, aby nie mylić stawki dystrybucji z pełną ceną zakupu.
- Dla `G14dynamic` szacowany koszt brutto jest liczony tylko wtedy, gdy dostępna jest pełna cena zakupu.

## 0.3.6

- Dodano taryfę `G14dynamic` dla operatora TAURON.
- Dodano oficjalne stawki brutto dystrybucji TAURON G14dynamic dla stref S1-S4.
- Dodano pobieranie dynamicznego harmonogramu stref z API PSE Energetyczny Kompas.
- Dodano obsługę własnych stawek S1-S4 dla taryfy G14dynamic.
- Zmieniono klasę IoT integracji na `cloud_polling`, ponieważ G14dynamic używa API PSE.

## 0.3.5

- Dodano taryfę `G13` dla operatora TAURON.
- Dodano preset cen brutto TAURON G13 wyliczony z oficjalnych stawek TAURON/URE 2026.
- Dodano obsługę trzech stref cenowych oraz sezonowego harmonogramu G13.
- Uwzględniono soboty, niedziele i polskie dni ustawowo wolne jako niską strefę cenową.

## 0.3.4

- Usunięto niezgodny `state_class` z sensora szacowanego kosztu brutto.
- Przeniesiono odczyt wbudowanych presetów cen poza pętlę zdarzeń Home Assistant.
- Dodano nazwę twórcy jako producenta urządzenia integracji widocznego w Home Assistant.

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
