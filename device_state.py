class DeviceState:
    """État de connexion ASCOM d'un appareil."""

    def __init__(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def set_connected(self, value: bool) -> None:
        self._connected = value
