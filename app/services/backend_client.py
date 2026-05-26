from datetime import datetime
from typing import Any

import httpx

from app.config import BACKEND_BASE_URL, IOT_JWT_TOKEN
from app.schemas.scenario_schema import SensorMeasurement

ROOM_ID = "shared"

ACTION_MAP = {
    "turn on":  "On",
    "turn off": "Off",
    "open":     "Open",
    "close":    "Closed",
}

DEVICE_MAP = {
    "Heater":  "Heater",
    "Windows": "Window",
    "Curtain": "Curtain",
}


class BackendClient:
    def __init__(
        self,
        base_url: str = BACKEND_BASE_URL,
        room_id: str = ROOM_ID,
        jwt_token: str = IOT_JWT_TOKEN,
    ):
        self.base_url = base_url.rstrip("/")
        self.room_id = room_id
        self.jwt_token = jwt_token

    async def send_device_action(self, device: str, action: str) -> dict:
        iot_device = DEVICE_MAP.get(device, device)
        iot_state = ACTION_MAP[action]

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.base_url}/devices/action",
                json={
                    "roomId": self.room_id,
                    "device": iot_device,
                    "state":  iot_state,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_current_sensor_data(self) -> SensorMeasurement:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/sensor-data/current",
                params={"roomId": self.room_id},
                headers={"Authorization": f"Bearer {self.jwt_token}"},
            )
            response.raise_for_status()
            payload = response.json()

        return self._parse_measurement(payload)

    def _parse_measurement(self, payload: Any) -> SensorMeasurement:
        if isinstance(payload, list):
            if not payload:
                raise ValueError("Backend returned an empty sensor-data list")

            payload = payload[-1]

        if not isinstance(payload, dict):
            raise ValueError("Backend returned unsupported sensor-data format")

        temperature = self._get_first_existing(
            payload,
            ["temperature", "Temperature", "temp", "currentTemperature"],
        )

        humidity = self._get_first_existing(
            payload,
            ["humidity", "Humidity", "currentHumidity"],
        )

        timestamp_raw = self._get_first_existing(
            payload,
            ["timestamp", "time", "createdAt", "created_at"],
            required=False,
        )

        timestamp = None

        if timestamp_raw:
            timestamp = datetime.fromisoformat(
                str(timestamp_raw).replace("Z", "+00:00")
            )

        return SensorMeasurement(
            temperature=float(temperature),
            humidity=float(humidity),
            timestamp=timestamp,
        )

    def _get_first_existing(
        self,
        payload: dict,
        keys: list[str],
        required: bool = True,
    ):
        for key in keys:
            if key in payload and payload[key] is not None:
                return payload[key]

        if required:
            raise ValueError(
                f"Backend response has no required field. Tried keys: {keys}"
            )

        return None


backend_client = BackendClient()