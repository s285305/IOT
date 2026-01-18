import time
import requests
import paho.mqtt.client as mqtt
import json
from mqtt_client import Client

class ComputeDecay(Client):
    def __init__(self, catalog_url: str):
        super().__init__( catalog_url, type='computeDecay')
        self._uri = catalog_url.rstrip("/")
        self._writer_url = requests.get(f"{self._uri}/c_d_url").json().get("c_d_url")

    def message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return

        # ignora config
        if data.get("message") == "config":
            return

        temperature = data.get("temperature")
        humidity = data.get("humidity")
        pole_id = data.get("id")
        timestamp = data.get("timestamp")

        if temperature is None or humidity is None or pole_id is None or timestamp is None:
            return

        decay = self.compute_decay(float(temperature), float(humidity))

        payload = {
            "pole_id": str(pole_id),
            "timestamp": int(timestamp),
            "decay": float(decay)
        }

        try:
            r = requests.post(f"{self._writer_url}/decay", json=payload, timeout=2)
            print(f"[*] Sent decay for pole {pole_id} at {timestamp}: {decay}")
            if r.status_code not in (200, 201):
                print(f"[!] Writer POST failed ({r.status_code}): {r.text}")
        except Exception as e:
            print(f"[!] Writer POST error: {e}")

    def compute_decay(self, temperature, humidity):
            # Formula for humidity 
            # constants for humidity
            c1 = 6.75e-10
            c2 = -3.5e-7
            c3 = 7.18e-5
            c4 = -7.22e-3
            c5 = 0.34
            c6 = -4.98

            if humidity < 25:
                du = 0
            else:
                du = c1*humidity**5 + c2*humidity**4 + c3*humidity**3 + c4*humidity**2 + c5*humidity + c6

            # Formula for temperature
            # constants for temperature
            c7  = -1.8e-6
            c8  = 9.57e-5
            c9  = -1.55e-3
            c10 = 4.17e-2

            if (temperature < 0.0) or (temperature > 40.0):
                dT = 0
            else:
                dT = c7*temperature**4 + c8*temperature**3 + c9*temperature**2 + c10*temperature

            # Formula di decay
            d = (3.2*dT + du) / 4.2
            
            return d



if __name__ == "__main__":
    computeDecay = ComputeDecay("http://localhost:8080")
    computeDecay.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
