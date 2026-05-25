# Changelog

## 0.2.1

- Fixed inconsistent options flow labels by replacing the remaining legacy
  `zone_1_rate` form field with `high_rate`.
- Kept fallbacks for existing `zone_1_rate` and `night_rate` configuration data.

## 0.2.0

- Replaced day/night wording with high/low price zone terminology.
- Added EMS-oriented sensors for current price zone, next zone change, minutes to zone change and forecast average price.
- Added binary sensors for low price zone and price below forecast average.
- Kept backward compatibility for existing `night_rate` options.

## 0.1.1

- Added an options flow for changing tariffs and rates after installation.
- Added HACS brand assets.
- Updated repository metadata and validation workflow.
- Fixed manifest links and code owner metadata.

## 0.1.0

- Initial Home Assistant custom integration skeleton.
- Added HACS structure, config flow, coordinator and sensor examples.
