import json
import requests
import paho.mqtt.client as mqtt


class CheckThreshold:
    def __init__(self, catalog_url, timeout: int = 5):
        self.catalog_url = catalog_url
        self.timeout = timeout
        self.broker = None
        self.backend_base = None   
        self.alert_base = None     
        self.threshold = None      # numero 
        self.client_id = "threshold-check"
        self.client = None

        self.register()
    
    def register(self):
        payload = {
            "type":"checkT",
            "id":self.client_id
        }
        r = requests.post(f"{self.catalog_url}/backend", json=payload)
        r.raise_for_status()
        print("[*] Registrazione al BackEnd riuscita")
        return r    

    def load_from_catalog(self):
        self.broker = requests.get(
            f"{self.catalog_url}/central_broker", timeout=self.timeout
        ).json()  # {address, port} 
        print(f"[*] Broker centrale ottenuto: {self.broker}")

        topics = requests.get(
            f"{self.catalog_url}/topic", timeout=self.timeout
        ).json()  # {backEnd, dashboard} 
        print(f"[*] Topics ottenuti: {topics}")
        self.backend_base = topics["backEnd"]
        self.alert_base = topics["dashboard"]

        # Catalog espone /threshold e ritorna un valore numerico (o null) 
        self.threshold = requests.get(
            f"{self.catalog_url}/threshold", timeout=self.timeout
        ).json()
        print(f"[*] Threshold ottenuta: {self.threshold}")

        if self.threshold['threshold'] is None:
            raise ValueError("Threshold non presente nel catalog (/threshold).")

    def start(self):
        if self.broker is None or self.backend_base is None or self.alert_base is None or self.threshold is None:
            self.load_from_catalog()

        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish

        self.client.connect(self.broker["address"], self.broker["port"])
        self.client.loop_forever()

    def _on_publish(self, client, userdata, mid, reason_code, properties):
        print(f"Message {mid} published.")

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        # Subscribe a tutti i gateway sul broker centrale: poleData/#
        client.subscribe(f"{self.backend_base}/#", qos=1)
        print(f"[*] Sottoscritto a {self.backend_base}/# per monitorare i tilt dei pali.")

    def _on_message(self, client, userdata, msg):
        # gateway_id preso dal topic: poleData/pole_id/<gateway_id> 
        try:
            gateway_id = msg.topic.split("/")[-1]
        except Exception:
            return

        try:
            data = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return

        pole_id = data.get("id")
        if not pole_id:
            return

        tilt = data.get("tilt")  # accelerometer measure nel publisher 
        if tilt is None or not isinstance(tilt, (int, float)):
            return

        if tilt <= self.threshold['threshold']:
            print(f"[!] Tilt {tilt} <= threshold {self.threshold['threshold']}")  # threshold unica dal catalog (/threshold) 
            return

        alert = {
            "gateway_id": gateway_id,
            "pole_id": pole_id,
            "sensor_type": "tilt",
            "value": tilt,
            "threshold": self.threshold['threshold']
        }

        alert_topic = f"{self.alert_base}/{gateway_id}/{pole_id}"  # alert/<gw>/<pole> 
        client.publish(alert_topic, json.dumps(alert), qos=1)
        print(f"[!] Alert pubblicato su {alert_topic}: {alert}")


if __name__ == "__main__":
    check_threshold = CheckThreshold("http://localhost:8080")
    check_threshold.start()