import os
import asyncio
import websockets
from datetime import datetime
from ocpp.routing import on
from ocpp.v16 import ChargePoint as CP
from ocpp.v16.enums import RegistrationStatus
from ocpp.v16 import call_result

connected_stations = {}

class ChargePoint(CP):
    @on("BootNotification")
    async def on_boot(self, charge_point_vendor, charge_point_model, **kwargs):
        print(f"[BOOT] {self.id} - {charge_point_vendor} {charge_point_model}")
        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(),
            interval=30,
            status=RegistrationStatus.accepted
        )

    @on("Heartbeat")
    async def on_heartbeat(self):
        print(f"[HEARTBEAT] {self.id}")
        return call_result.HeartbeatPayload(
            current_time=datetime.utcnow().isoformat()
        )

    @on("StatusNotification")
    async def on_status(self, connector_id, error_code, status, **kwargs):
        print(f"[STATUS] {self.id} | Conn {connector_id} | {status} | {error_code}")
        return call_result.StatusNotificationPayload()

async def main():
    async def on_connect(websocket, path):
        parts = path.strip("/").split("/")
        if len(parts) >= 2:
            backend = parts[0]
            cp_id = parts[1]
        else:
            backend = "DEFAULT"
            cp_id = parts[0] if parts else "UNKNOWN"

        print(f"[CONNECT] backend={backend} cp_id={cp_id}")
        cp = ChargePoint(cp_id, websocket)
        connected_stations[cp_id] = websocket
        await cp.start()

    port = int(os.environ.get("PORT", 8080))
    server = await websockets.serve(
        on_connect,
        "0.0.0.0",
        port,
        subprotocols=["ocpp1.6"]
    )
    print(f"🟢 Serveur OCPP INTELEC-IRVE lancé sur port {port}")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
