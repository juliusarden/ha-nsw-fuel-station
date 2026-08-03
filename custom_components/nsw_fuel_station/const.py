"""Constants for NSW Fuel Station integration."""

DOMAIN = "nsw_fuel_station"
CONF_STATION_ID = "station_id"
CONF_FUEL_TYPES = "fuel_types"
CONF_STATION_NAME = "station_name"

# All possible fuel types
FUEL_TYPES = [
    "E10", "U91", "E85", "P95", "P98",
    "DL", "PDL", "B20", "LPG", "CNG", "EV"
]

DEFAULT_FUEL_TYPES = ["E10", "U91"]
UPDATE_INTERVAL = 30  # minutes

# Default NSW home coordinates for average tracking
DEFAULT_LATITUDE = -33.66
DEFAULT_LONGITUDE = 150.91