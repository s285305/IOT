import json
import time
import requests
import paho.mqtt.client as mqtt
from mqtt_client import Client


class CheckThreshold (Client):
    def __init__(self, catalog_url):
        super().__init__( catalog_url, type='checkThreshold')
        self.catalog_url = catalog_url
        self.load_from_catalog()     # numero 
    
    def connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connection status: {reason_code}")
        # Automatically subscribe to topics found in catalog upon connection
        for topic in self.topics['subscribe']:
            client.subscribe(f'{topic}/#')
            print(f"Subscribed to {topic}")

    def subscribe(self, topic, qos=0):
        if topic not in self.topics["subscribe"]:
            try:
                self.client.subscribe(topic + '/#', qos)
                self.topics["subscribe"].append(topic)
                data = {'new_topics': self.topics}
                requests.put(f'{self.catalog_url}/topic', params=[('type', self.type)], json=data)
                print(f'Successfully subscribed to {topic}/#')
            except Exception as e:
                print('Impossible to subscribe, error: ', e)
        else:
            print(f"Already subscribed to topic {topic}")

    def load_from_catalog(self):
        # Catalog espone /threshold e ritorna un valore numerico (o null) 
        self.threshold = requests.get(
            f"{self.catalog_url}/threshold").json()
        print(f"[*] Threshold ottenuta: {self.threshold}")

        if self.threshold['threshold'] is None:
            raise ValueError("Threshold non presente nel catalog (/threshold).")

    def message(self, client, userdata, msg):
        
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
        for topic in self.topics["publish"]:
            self.alert_base = topic  # alert/<gateway_id>/<pole_id>
            alert_topic = f"{self.alert_base}/{gateway_id}/{pole_id}"  # alert/<gw>/<pole> 
            self.client.publish(alert_topic, json.dumps(alert), qos=1)
            print(f"[!] Alert pubblicato su {alert_topic}: {alert}")




if __name__ == "__main__":
    check_threshold = CheckThreshold("http://localhost:8080")
    check_threshold.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        check_threshold.client.loop_stop()