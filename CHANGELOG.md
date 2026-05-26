# Changelog

## 0.3.2

- Rounded gross price sensors and forecast price attributes to two decimal places.
- Added suggested display precision for price and time-to-change sensors.

## 0.3.1

- Split configuration into two steps so custom gross price fields are shown only
  when the custom price source is selected.
- Updated Polish configuration labels and descriptions.

## 0.3.0

- Reworked pricing model around gross `PLN/kWh` prices.
- Added bundled 2026 presets sourced from `cena-pradu.pl`.
- Added G11 presets per operator and average G12/G12w presets.
- Removed distribution, fixed monthly fee and VAT fields from the integration.
- Changed integration IoT class to `local_polling` because presets are bundled.

## 0.2.2

- Removed temporary compatibility fallbacks for `zone_1_rate` and `night_rate`
  during the testing phase.

## 0.2.1

- Fixed inconsistent options flow labels by replacing the remaining legacy
  `zone_1_rate` form field with `high_rate`.

## 0.2.0

- Replaced day/night wording with high/low price zone terminology.
- Added EMS-oriented sensors for current price zone, next zone change, minutes to zone change and forecast average price.
- Added binary sensors for low price zone and price below forecast average.

## 0.1.1

- Added an options flow for changing tariffs and rates after installation.
- Added HACS brand assets.
- Updated repository metadata and validation workflow.
- Fixed manifest links and code owner metadata.

## 0.1.0

- Initial Home Assistant custom integration skeleton.
- Added HACS structure, config flow, coordinator and sensor examples.
