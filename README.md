# Better NSW Fuel Station for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-juliusarden-yellow?logo=buymeacoffee)](https://buymeacoffee.com/juliusarden)

A custom Home Assistant integration for NSW (Australia) fuel prices from the NSW FuelCheck API. **Search by suburb, see prices on a map, compare against the NSW daily average.**

## Features

| Feature | Built-in | This |
|---------|----------|------|
| UI config flow | ❌ YAML only | ✅ Search by suburb or enter ID |
| Suburb search | ❌ | ✅ Type suburb, pick station from list |
| Map view | ❌ | ✅ Device tracker with station location |
| NSW average comparison | ❌ | ✅ Below/above state daily average |
| Per-station fuel types | ❌ | ✅ Each station configures its own fuels |
| Graceful errors | ❌ Crashes | ✅ Skips unavailable fuel types |

## Installation

### HACS (recommended)
1. HACS > Integrations > ⋮ > Custom repositories
2. URL: `https://github.com/juliusarden/ha-nsw-fuel-station`
3. Category: Integration → Install → Restart HA

### Manual
Copy `custom_components/nsw_fuel_station/` to `config/custom_components/`.

## Setup

1. **Settings → Devices & Services → Add Integration** → "NSW Fuel Station"
2. Choose **Search by suburb** and type your suburb (e.g. "Parramatta")
3. Pick your station from the list
4. Select fuel types (U91, E10, P98, Diesel, etc.)
5. The station appears on your HA map with live prices in the popup

## Entities created per station

For station tracking U91:

- `sensor.*_u91` — U91 price (¢/L)
- `binary_sensor.*_u91_below_avg` — ON if below NSW daily average
- `device_tracker.*` — Station location on HA map (with prices in attributes)

## Support

If this saves you money on fuel, consider [buying me a coffee ☕](https://buymeacoffee.com/juliusarden)

## License

MIT