import os

JEEDOM_STATUS_URL = os.environ.get(
    "OUKA_JEEDOM_URL",
    "https://XXX",
)

CACHE_TTL_SECONDS = int(os.environ.get("OUKA_CACHE_TTL", "30"))
HOST = os.environ.get("OUKA_HOST", "0.0.0.0")
PORT = int(os.environ.get("OUKA_PORT", "11111"))

SERVER_NAME = "Ouka Alpaca"
MANUFACTURER = "Ouka"
MANUFACTURER_VERSION = "1.0.0"
LOCATION = "Observatoire"
