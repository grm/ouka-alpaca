import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request

from alpaca_response import (
    alpaca_error,
    alpaca_ok,
    not_connected,
    parse_bool_param,
    read_only_error,
)
from device_state import DeviceState
from config import (
    HOST,
    LOCATION,
    MANUFACTURER,
    MANUFACTURER_VERSION,
    PORT,
    SERVER_NAME,
)
from roof_status import RoofStatusClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

roof = RoofStatusClient()
dome_state = DeviceState()
safety_state = DeviceState()

DOME_DEVICE = {
    "DeviceName": "Ouka Dome",
    "DeviceType": "Dome",
    "DeviceNumber": 0,
    "UniqueID": "ouka-dome-001",
}

SAFETY_DEVICE = {
    "DeviceName": "Ouka Weather Safety",
    "DeviceType": "SafetyMonitor",
    "DeviceNumber": 0,
    "UniqueID": "ouka-safety-001",
}

CONFIGURED_DEVICES = [DOME_DEVICE, SAFETY_DEVICE]

app = FastAPI(title=SERVER_NAME, version=MANUFACTURER_VERSION)


# --- Management API ---


@app.get("/management/v1/description")
async def management_description(request: Request):
    return alpaca_ok(
        request,
        {
            "ServerName": SERVER_NAME,
            "Manufacturer": MANUFACTURER,
            "ManufacturerVersion": MANUFACTURER_VERSION,
            "Location": LOCATION,
        },
    )


@app.get("/management/v1/configureddevices")
async def management_configured_devices(request: Request):
    return alpaca_ok(request, CONFIGURED_DEVICES)


# --- Helpers communs ---


def _common_get(
    device_name: str,
    description: str,
    interface_version: int,
    state: DeviceState,
):
    async def connected(request: Request):
        return alpaca_ok(request, state.is_connected())

    async def connecting(request: Request):
        return alpaca_ok(request, False)

    async def description_handler(request: Request):
        return alpaca_ok(request, description)

    async def driverinfo(request: Request):
        return alpaca_ok(
            request,
            f"{description}\nStatut Jeedom (cache 30s). Ouverture via API key Jeedom, pas de fermeture.",
        )

    async def driverversion(request: Request):
        return alpaca_ok(request, MANUFACTURER_VERSION)

    async def interfaceversion(request: Request):
        return alpaca_ok(request, interface_version)

    async def name(request: Request):
        return alpaca_ok(request, device_name)

    async def supportedactions(request: Request):
        return alpaca_ok(request, [])

    async def put_connected(request: Request):
        state.set_connected(await parse_bool_param(request, "Connected"))
        return alpaca_ok(request, None)

    async def put_connect(request: Request):
        state.set_connected(True)
        return alpaca_ok(request, None)

    async def put_disconnect(request: Request):
        state.set_connected(False)
        return alpaca_ok(request, None)

    async def put_action(request: Request):
        return read_only_error(request)

    async def put_command_blind(request: Request):
        return read_only_error(request)

    async def put_command_bool(request: Request):
        return read_only_error(request)

    async def put_command_string(request: Request):
        return read_only_error(request)

    return {
        "connected": connected,
        "connecting": connecting,
        "description": description_handler,
        "driverinfo": driverinfo,
        "driverversion": driverversion,
        "interfaceversion": interfaceversion,
        "name": name,
        "supportedactions": supportedactions,
        "put_connected": put_connected,
        "put_connect": put_connect,
        "put_disconnect": put_disconnect,
        "put_action": put_action,
        "put_command_blind": put_command_blind,
        "put_command_bool": put_command_bool,
        "put_command_string": put_command_string,
    }


_dome_common = _common_get(
    "Ouka Dome",
    "Toit coulissant Ouka (statut Jeedom, lecture seule)",
    interface_version=3,
    state=dome_state,
)
_safety_common = _common_get(
    "Ouka Weather Safety",
    "Sécurité météo dérivée de l'état du toit (vert = ouvert)",
    interface_version=1,
    state=safety_state,
)


def _register_common_routes(prefix: str, handlers: dict, devicestate_handler):
    app.add_api_route(
        f"{prefix}/connected",
        handlers["connected"],
        methods=["GET"],
    )
    app.add_api_route(
        f"{prefix}/connecting",
        handlers["connecting"],
        methods=["GET"],
    )
    app.add_api_route(
        f"{prefix}/description",
        handlers["description"],
        methods=["GET"],
    )
    app.add_api_route(
        f"{prefix}/driverinfo",
        handlers["driverinfo"],
        methods=["GET"],
    )
    app.add_api_route(
        f"{prefix}/driverversion",
        handlers["driverversion"],
        methods=["GET"],
    )
    app.add_api_route(
        f"{prefix}/interfaceversion",
        handlers["interfaceversion"],
        methods=["GET"],
    )
    app.add_api_route(
        f"{prefix}/name",
        handlers["name"],
        methods=["GET"],
    )
    app.add_api_route(
        f"{prefix}/supportedactions",
        handlers["supportedactions"],
        methods=["GET"],
    )
    app.add_api_route(
        f"{prefix}/devicestate",
        devicestate_handler,
        methods=["GET"],
    )
    app.add_api_route(
        f"{prefix}/connected",
        handlers["put_connected"],
        methods=["PUT"],
    )
    app.add_api_route(
        f"{prefix}/connect",
        handlers["put_connect"],
        methods=["PUT"],
    )
    app.add_api_route(
        f"{prefix}/disconnect",
        handlers["put_disconnect"],
        methods=["PUT"],
    )
    app.add_api_route(
        f"{prefix}/action",
        handlers["put_action"],
        methods=["PUT"],
    )
    app.add_api_route(
        f"{prefix}/commandblind",
        handlers["put_command_blind"],
        methods=["PUT"],
    )
    app.add_api_route(
        f"{prefix}/commandbool",
        handlers["put_command_bool"],
        methods=["PUT"],
    )
    app.add_api_route(
        f"{prefix}/commandstring",
        handlers["put_command_string"],
        methods=["PUT"],
    )


# --- Dome (lecture seule, toit coulissant) ---

DOME_PREFIX = "/api/v1/dome/0"


async def dome_shutterstatus(request: Request):
    if not dome_state.is_connected():
        return not_connected(request)
    return alpaca_ok(request, roof.shutter_state())


async def dome_slewing(request: Request):
    if not dome_state.is_connected():
        return not_connected(request)
    return alpaca_ok(request, False)


async def _require_dome_connected(request: Request):
    if not dome_state.is_connected():
        return not_connected(request)
    return None


async def dome_can_false(request: Request):
    if err := await _require_dome_connected(request):
        return err
    return alpaca_ok(request, False)


async def dome_can_setshutter(request: Request):
    if err := await _require_dome_connected(request):
        return err
    return alpaca_ok(request, True)


async def dome_close_not_supported(request: Request):
    if err := await _require_dome_connected(request):
        return err
    return alpaca_error(
        request,
        0x40B,
        "Fermeture non gérée : le toit se ferme manuellement via Jeedom",
    )


async def dome_openshutter(request: Request):
    if err := await _require_dome_connected(request):
        return err
    ok, detail = roof.request_open()
    if not ok:
        return alpaca_error(request, 0x500, f"Échec demande ouverture Jeedom : {detail}")
    return alpaca_ok(request, None)


async def dome_bool_false(request: Request):
    if err := await _require_dome_connected(request):
        return err
    return alpaca_ok(request, False)


async def dome_azimuth(request: Request):
    if err := await _require_dome_connected(request):
        return err
    return alpaca_ok(request, 0.0)


async def dome_altitude(request: Request):
    if err := await _require_dome_connected(request):
        return err
    return alpaca_ok(request, 90.0)


async def dome_devicestate(request: Request):
    if not dome_state.is_connected():
        return not_connected(request)
    return alpaca_ok(
        request,
        [
            {"Name": "Connected", "Value": True},
            {"Name": "CanSetShutter", "Value": True},
            {"Name": "ShutterStatus", "Value": roof.shutter_state()},
            {"Name": "Azimuth", "Value": 0.0},
            {"Name": "Altitude", "Value": 90.0},
            {"Name": "AtHome", "Value": False},
            {"Name": "AtPark", "Value": False},
            {"Name": "Slaved", "Value": False},
            {"Name": "Slewing", "Value": False},
            {"Name": "TimeStamp", "Value": datetime.now(timezone.utc).isoformat()},
        ],
    )


_register_common_routes(DOME_PREFIX, _dome_common, dome_devicestate)

# GET statut
app.add_api_route(f"{DOME_PREFIX}/shutterstatus", dome_shutterstatus, methods=["GET"])
app.add_api_route(f"{DOME_PREFIX}/slewing", dome_slewing, methods=["GET"])

for cap in (
    "canfindhome",
    "canpark",
    "cansetaltitude",
    "cansetazimuth",
    "cansetpark",
    "canslave",
    "cansyncazimuth",
):
    app.add_api_route(f"{DOME_PREFIX}/{cap}", dome_can_false, methods=["GET"])

app.add_api_route(f"{DOME_PREFIX}/cansetshutter", dome_can_setshutter, methods=["GET"])

app.add_api_route(f"{DOME_PREFIX}/azimuth", dome_azimuth, methods=["GET"])
app.add_api_route(f"{DOME_PREFIX}/altitude", dome_altitude, methods=["GET"])

for prop in ("athome", "atpark", "slaved"):
    app.add_api_route(f"{DOME_PREFIX}/{prop}", dome_bool_false, methods=["GET"])

app.add_api_route(f"{DOME_PREFIX}/openshutter", dome_openshutter, methods=["PUT"])
app.add_api_route(f"{DOME_PREFIX}/closeshutter", dome_close_not_supported, methods=["PUT"])

for action in (
    "abortslew",
    "findhome",
    "park",
    "setpark",
    "slewtoaltitude",
    "slewtoazimuth",
    "synctoazimuth",
    "slaved",
):
    app.add_api_route(f"{DOME_PREFIX}/{action}", read_only_error, methods=["PUT"])


# --- SafetyMonitor (lecture seule, dérivé du toit) ---

SAFETY_PREFIX = "/api/v1/safetymonitor/0"


async def safety_issafe(request: Request):
    if not safety_state.is_connected():
        return not_connected(request)
    is_open = roof.is_open()
    if is_open is None:
        return alpaca_error(
            request,
            0x500,
            "Impossible de lire l'état du toit depuis Jeedom",
            False,
        )
    return alpaca_ok(request, is_open)


async def safety_devicestate(request: Request):
    if not safety_state.is_connected():
        return not_connected(request)
    is_open = roof.is_open()
    safe = is_open if is_open is not None else False
    return alpaca_ok(
        request,
        [
            {"Name": "IsSafe", "Value": safe},
            {"Name": "TimeStamp", "Value": datetime.now(timezone.utc).isoformat()},
        ],
    )


_register_common_routes(SAFETY_PREFIX, _safety_common, safety_devicestate)
app.add_api_route(f"{SAFETY_PREFIX}/issafe", safety_issafe, methods=["GET"])


@app.get("/")
async def root():
    return {
        "server": SERVER_NAME,
        "devices": CONFIGURED_DEVICES,
        "docs": "https://ascom-standards.org/api/",
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Démarrage %s sur %s:%s", SERVER_NAME, HOST, PORT)
    uvicorn.run(app, host=HOST, port=PORT)
