import json, queue, threading, time
import paho.mqtt.client as mqtt
from influxdb_client_3 import InfluxDBClient3, Point
import requests  

catalog_url="http://localhost:8080"
Q = queue.Queue(maxsize=5000)

def get_broker_central(catalog_url):
        resp_broker = requests.get(f"{catalog_url}/central_broker")
        central_broker_conf = resp_broker.json()
        print(f"[*] Broker Centrale ottenuto: {central_broker_conf}")
        return central_broker_conf

def compute_decay(temperature, humidity):
    if temperature < 2 or humidity < 80:
        return 0.0
    risk = (temperature - 2) * (humidity - 80) / 7.5
    return round(min(100.0, max(0.0, risk)), 2)

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    if data.get("message") == "config":
        return  # ignore config packets 
    Q.put((msg.topic, data), block=False)

def influx_writer_loop(influx: InfluxDBClient3, database: str):
    while True:
        topic, data = Q.get()
        pole_id = data.get("id")
        ts = data.get("timestamp")          
        temp = data.get("temperature")
        hum  = data.get("humidity")
        tilt = data.get("tilt")

        decay = compute_decay(temp, hum)

        # Derive gateway_id from topic
        gateway_id = topic.split("/")[-1] if "/" in topic else "unknown"

        p = (
            Point("pole_measurements")
            .tag("pole_id", str(pole_id))
            .tag("gateway_id", str(gateway_id))
            .field("temperature", float(temp))
            .field("humidity", float(hum))
            .field("tilt", float(tilt))
            .field("decay", float(decay))
            .time(int(ts), write_precision="s")
        )
        influx.write(database=database, record=p)  # Point-based write

    

def main():
    INFLUX_HOST = "http://localhost:8181"
    INFLUX_TOKEN = "apiv3_qkhm2kiMdFeqH7127QV_5-6dak5IwIrzr7Fy85eEnYpyXs2o46NdAvqqYm8BLUOWKxAO83-3UuoB9A9ikLpXVQ"   # your admin token
    DB = "pole_measurements"

    influx = InfluxDBClient3(host=INFLUX_HOST, token=INFLUX_TOKEN, database=DB)  # client usage [web:19]

    t = threading.Thread(target=influx_writer_loop, args=(influx, DB), daemon=True)
    t.start()

    m = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    m.on_message = on_message
    broker= get_broker_central(catalog_url)
    m.connect(broker["address"], broker['port'])  # central broker catalog
    m.subscribe("poleData/#")     
    m.loop_forever()

if __name__ == "__main__":
    main()
