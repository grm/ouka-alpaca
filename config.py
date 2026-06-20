import os
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

JEEDOM_STATUS_URL = os.environ.get(
    "OUKA_JEEDOM_URL",
    "https://XXX",
)

JEEDOM_OPEN_CMD_ID = int(os.environ.get("OUKA_JEEDOM_OPEN_CMD_ID", "302"))


def _jeedom_cmd_url(cmd_id: int) -> str:
    """Construit l'URL Jeedom pour une commande (même apikey que OUKA_JEEDOM_URL)."""
    parsed = urlparse(JEEDOM_STATUS_URL)
    params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    params["type"] = "cmd"
    params["id"] = str(cmd_id)
    return urlunparse(parsed._replace(query=urlencode(params)))


JEEDOM_OPEN_URL = _jeedom_cmd_url(JEEDOM_OPEN_CMD_ID)

CACHE_TTL_SECONDS = int(os.environ.get("OUKA_CACHE_TTL", "30"))
HOST = os.environ.get("OUKA_HOST", "0.0.0.0")
PORT = int(os.environ.get("OUKA_PORT", "11111"))

SERVER_NAME = "Ouka Alpaca"
MANUFACTURER = "Ouka"
MANUFACTURER_VERSION = "1.0.0"
LOCATION = "Observatoire"
