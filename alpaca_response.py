import json
from typing import Any
from urllib.parse import parse_qs

from fastapi import Request
from fastapi.responses import JSONResponse

# Codes d'erreur ASCOM (Alpaca)
ERR_METHOD_NOT_IMPLEMENTED = 0x400
ERR_PROPERTY_NOT_IMPLEMENTED = 0x401
ERR_NOT_CONNECTED = 0x407
ERR_INVALID_OPERATION = 0x40B

_server_transaction_id = 0


def _next_server_transaction_id() -> int:
    global _server_transaction_id
    _server_transaction_id += 1
    return _server_transaction_id


def _client_ids(request: Request) -> tuple[int, int]:
    client_id = int(request.query_params.get("ClientID", 0))
    client_transaction_id = int(request.query_params.get("ClientTransactionID", 0))
    return client_id, client_transaction_id


def alpaca_ok(request: Request, value: Any) -> JSONResponse:
    client_id, client_transaction_id = _client_ids(request)
    return JSONResponse(
        {
            "Value": value,
            "ClientTransactionID": client_transaction_id,
            "ServerTransactionID": _next_server_transaction_id(),
            "ClientID": client_id,
            "ErrorNumber": 0,
            "ErrorMessage": "",
        }
    )


def alpaca_error(
    request: Request,
    error_number: int,
    error_message: str,
    value: Any = None,
) -> JSONResponse:
    client_id, client_transaction_id = _client_ids(request)
    return JSONResponse(
        {
            "Value": value,
            "ClientTransactionID": client_transaction_id,
            "ServerTransactionID": _next_server_transaction_id(),
            "ClientID": client_id,
            "ErrorNumber": error_number,
            "ErrorMessage": error_message,
        }
    )


def read_only_error(request: Request) -> JSONResponse:
    return alpaca_error(
        request,
        ERR_INVALID_OPERATION,
        "Lecture seule : le toit est contrôlé via Jeedom",
    )


def property_not_implemented(request: Request) -> JSONResponse:
    return alpaca_error(
        request,
        ERR_PROPERTY_NOT_IMPLEMENTED,
        "Propriété non implémentée pour ce toit coulissant",
    )


def not_connected(request: Request) -> JSONResponse:
    return alpaca_error(request, ERR_NOT_CONNECTED, "not connected")


async def parse_bool_param(request: Request, name: str, default: bool = False) -> bool:
    if name in request.query_params:
        return request.query_params[name].lower() in ("true", "1")

    body = await request.body()
    if not body:
        return default

    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        return default

    try:
        data = json.loads(text)
        if isinstance(data, dict) and name in data:
            return bool(data[name])
    except json.JSONDecodeError:
        pass

    parsed = parse_qs(text, keep_blank_values=True)
    if name in parsed:
        return parsed[name][0].lower() in ("true", "1")

    return default
