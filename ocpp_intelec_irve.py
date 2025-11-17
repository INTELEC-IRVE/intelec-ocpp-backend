import os
import asyncio
import websockets
from datetime import datetime

# ============================================================
# PATCH DE COMPATIBILITÉ JSONSCHEMA POUR OCPP (Render / OCPP 0.18)
# ============================================================
import jsonschema
try:
    # jsonschema < 4.x
    from jsonschema import _validators  # noqa: F401
except ImportError:
    # jsonschema >= 4.x : recréer _validators à partir de validators
    from jsonschema import validators as _validators  # noqa: F401
    jsonschema._validators = _validators
# ============================================================

from ocpp.routing import on
from ocpp.v16 import ChargePoint as CP
from ocpp.v16.enums import RegistrationStatus
from ocpp.v16 import call_result

connected_stations = {}


class ChargePoint(CP):

    @on("BootNotification")
    async def on_boot(self, charge_point_vendor, charge_point_model, **kwargs):
        print(f"[BOOT] {self.id} - vendor={charge_point_vendor} model={charge_point_model}")
        return call_result.BootNotificationPayload(
            status=RegistrationStatus.accepted,
            current_time=datetime.utcnow().isoformat(),
            interval=10,
        )

    @on("StatusNotification")
    async def on_status(self, connector_id, error_code, status, **kwargs):
        print(f"[STATUS] {self.id} | conn {connector_id} | {status} | {error_code}")
        return call_result.StatusNotificationPayload()

    async def on_heartbeat(self):
        print(f"[HEARTBEAT] {self.id}")
        return call_result.HeartbeatPayload()


async def on_connect(websocket, path):
    parts = path.strip("/").split("/")
    if len(parts) > 1:
        cp_id = parts[1]
    else:
        cp_id = "UNKNOWN"

    print(f"[CONNECT] backend={parts[0]} | id={cp_id}")

    cp = ChargePoint(cp_id, websocket)
    connected_stations[cp_id] = websocket
    await cp.start()


async def main():
    # Render impose PORT via variable d'environnement
    port = int(os.environ.get("PORT", 8080))

    print(f"🚀 Serveur OCPP INTELEC-IRVE lancé sur le port {port}")

    server = await websockets.serve(
        on_connect,
        host="0.0.0.0",
        port=port,
        subprotocols=["ocpp1.6"]
    )

    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())

