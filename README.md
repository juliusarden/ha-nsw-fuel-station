# Better NSW Fuel Station for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A custom Home Assistant integration for NSW (Australia) fuel prices from the NSW FuelCheck API.

## Why use this instead of the built-in one?

| Feature | Built-in | This |
|---------|----------|------|
| UI config flow | ❌ YAML only | ✅ Add via Settings > Integrations |
| Graceful fuel types | ❌ Crashes if fuel unavailable | ✅ Ignores missing fuels |
| Entity naming | Generic | `sensor.nsw_fuel_20067_e10` |
| Per-station entries | ❌ | ✅ Each station is its own entry |
| Multiple stations | One YAML block | Individual config entries |

## Installation

### HACS (recommended)
1. HACS > Integrations > ⋮ > Custom repositories
2. URL: `https://github.com/juliusarden/ha-nsw-fuel-station`
3. Category: Integration
4. Install and restart HA

### Manual
Copy `custom_components/nsw_fuel_station/` to your HA `config/custom_components/` directory.

## Setup

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for "NSW Fuel Station"
3. Enter the Station ID from [fuelcheck.nsw.gov.au](https://www.fuelcheck.nsw.gov.au/app)
4. Select which fuel types to track (E10, U91, P98, Diesel, etc.)
5. Repeat for additional stations

### Finding a Station ID
1. Open [fuelcheck.nsw.gov.au/app](https://www.fuelcheck.nsw.gov.au/app)
2. Search your suburb, tap a station
3. Click "Report this Station" — the `serviceStationId` is in the URL

## Entities created

For station `20067` tracking E10, U91, P98:

- `sensor.nsw_fuel_20067_e10` — E10 price (¢/L)
- `sensor.nsw_fuel_20067_u91` — Unleaded 91 price (¢/L)
- `sensor.nsw_fuel_20067_p98` — Premium 98 price (¢/L)

## License

MIT