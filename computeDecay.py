import time
import requests
import paho.mqtt.client as mqtt
import json


class ComputeDecay:
    lista = []

    def __init__(self, catalog_url: str, writer_url: str):
        self._uri = catalog_url.rstrip("/")
        self._writer_url = writer_url.rstrip("/")
        self._broker = {}
        self._topic = "#"

        self._clientId = f"ComputeDecay_{len(ComputeDecay.lista)}"
        ComputeDecay.lista.append(self._clientId)

        # gets connection info from catalog and registers its id, client REST
        self.get_connection_info()
        self.register()

        # MQTT subscriber to get measurements data
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=self._clientId
        )

        # register callbacks
        self.client.on_connect = self.connect
        self.client.on_message = self.on_message

        self.client.connect(self._broker['address'], int(self._broker['port']))
        self.client.loop_start()

        self.client.subscribe(self._topic, qos=1)

    def get_connection_info(self):
        broker = requests.get(f"{self._uri}/central_broker").json()
        self._broker['address'] = broker['address']
        self._broker['port'] = broker['port']

        back_end = requests.get(f"{self._uri}/topic").json()['backEnd']  # "poleData" [file:199]
        self._topic = f"{back_end}/#"
        return self._broker, self._topic

    def register(self):
        payload = {
            "type": "ComputeDecay",
            "id": self._clientId
        }
        r = requests.post(f"{self._uri}/backend", json=payload)
        r.raise_for_status()
        print("[*] Registrazione al BackEnd riuscita")
        return r

    def connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connection status: {str(reason_code)}")
        print(f"Subscribed to: {self._topic}")

    def on_message(self, client, userdata, msg):
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
    computeDecay = ComputeDecay("http://localhost:8080", "http://localhost:8090")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
