import json
import time
import threading
import cherrypy
import requests
import paho.mqtt.client as mqtt
from influxdb_client_3 import InfluxDBClient3, Point
from mqtt_client import Client

class InfluxWriter:
    def __init__(self, host: str, token: str, database: str, table: str = "pole_measurements"):
        self.database = database
        self.table = table
        self.client = InfluxDBClient3(host=host, token=token, database=database)

    def write_joined(self, pole_id: str, gateway_id: str, ts: int, temperature: float, humidity: float, tilt: float, decay: float):
        p = (
            Point(self.table)
            .tag("pole_id", str(pole_id))
            .tag("gateway_id", str(gateway_id))
            .field("temperature", float(temperature))
            .field("humidity", float(humidity))
            .field("tilt", float(tilt))
            .field("decay", float(decay))
            .time(int(ts), write_precision="s")
        )
        self.client.write(database=self.database, record=p)


class JoinBuffer:
    """
    Join by (pole_id, timestamp). TTL cleanup to avoid infinite growth.
    """
    def __init__(self, ttl_s: int = 300):
        self.ttl_s = ttl_s
        self.mqtt_cache = {}   # (pole_id, ts) -> mqtt packet dict
        self.decay_cache = {}  # (pole_id, ts) -> decay float
        self.lock = threading.Lock()

    def put_mqtt(self, pole_id: str, ts: int, pkt: dict):
        key = (str(pole_id), int(ts))
        with self.lock:
            self.mqtt_cache[key] = pkt

    def put_decay(self, pole_id: str, ts: int, decay: float):
        key = (str(pole_id), int(ts))
        with self.lock:
            self.decay_cache[key] = float(decay)

    def pop_if_join_ready(self, pole_id: str, ts: int):
        key = (str(pole_id), int(ts))
        with self.lock:
            if key in self.mqtt_cache and key in self.decay_cache:
                pkt = self.mqtt_cache.pop(key)
                decay = self.decay_cache.pop(key)
                return pkt, decay
        return None, None

    def gc(self):
        now = int(time.time())
        with self.lock:
            self.mqtt_cache = {
                k: v for k, v in self.mqtt_cache.items()
                if (now - int(v.get("timestamp", now))) <= self.ttl_s
            }
            self.decay_cache = {
                k: v for k, v in self.decay_cache.items()
                if (now - int(k[1])) <= self.ttl_s
            }


class WriterCore(Client):
    def __init__(self, catalog_url):
        super().__init__(catalog_url, type='interfaccia')
        self.http_port = 0
        self.influx_host = ''
        self.influx_token =''
        self.influx_db = ''
        self.table=''
        self.get_influxdb_info()
        self.join = JoinBuffer(ttl_s=300)
        self.influx = InfluxWriter(self.influx_host, 
                                   self.influx_token, 
                                   self.influx_db, 
                                   self.table
                                   )

        self._gc_thread = threading.Thread(target=self._gc_loop, daemon=True)
        self._gc_thread.start()

    def get_influxdb_info(self):
        try:
            self.http_port = requests.get(f"{self.catalog_url}/writer_port").json().get("writer_port", 8090)
            self.influx_host = requests.get(f"{self.catalog_url}/db_info").json().get("influx_host", "http://localhost:8181")
            self.influx_token = requests.get(f"{self.catalog_url}/db_info").json().get("token", "")
            self.influx_db = requests.get(f"{self.catalog_url}/db_info").json().get("db", "pole_measurements")
            self.table = requests.get(f"{self.catalog_url}/db_info").json().get("table", "pole_measurements")
        except Exception as e:
            print('Error in GET influxdb info, error: ',e)

    def message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return

        if data.get("message") == "config":
            return

        pole_id = data.get("id")
        ts = data.get("timestamp")
        if pole_id is None or ts is None:
            return

        # Convention: gateway publishes to central as .../<gateway_id> 
        gateway_id = msg.topic.split("/")[-1] if "/" in msg.topic else "unknown"

        pkt = {
            "pole_id": str(pole_id),
            "timestamp": int(ts),
            "gateway_id": str(gateway_id),
            "temperature": data.get("temperature"),
            "humidity": data.get("humidity"),
            "tilt": data.get("tilt"),
        }

        self.join.put_mqtt(pole_id, ts, pkt)

        # if decay already arrived, write now
        joined_pkt, decay = self.join.pop_if_join_ready(pole_id, ts)
        if joined_pkt is not None:
            self._write(joined_pkt, decay)

    def submit_decay(self, pole_id: str, ts: int, decay: float) -> dict:
        self.join.put_decay(pole_id, ts, decay)

        joined_pkt, decay_val = self.join.pop_if_join_ready(pole_id, ts)
        if joined_pkt is not None:
            self._write(joined_pkt, decay_val)
            return {"status": "written"}
        return {"status": "cached_waiting_mqtt"}

    def _write(self, pkt: dict, decay: float):
        self.influx.write_joined(
            pole_id=pkt["pole_id"],
            gateway_id=pkt["gateway_id"],
            ts=int(pkt["timestamp"]),
            temperature=float(pkt["temperature"]),
            humidity=float(pkt["humidity"]),
            tilt=float(pkt["tilt"]),
            decay=float(decay),
        )
        print(f"[v] Written joined point pole={pkt['pole_id']} ts={pkt['timestamp']} gateway={pkt['gateway_id']} decay={decay}")

    def _gc_loop(self):
        while True:
            time.sleep(10)
            self.join.gc()


class DecayAPI:
    exposed = True

    def __init__(self, core: WriterCore):
        self.core = core

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri, **params):
        body = cherrypy.request.json
        pole_id = body.get("pole_id")
        ts = body.get("timestamp")
        decay = body.get("decay")
        if pole_id is None or ts is None or decay is None:
            raise cherrypy.HTTPError(400, "Missing pole_id/timestamp/decay")
        return self.core.submit_decay(pole_id, int(ts), float(decay))


class Root:
    def __init__(self, core: WriterCore):
        self.decay = DecayAPI(core)  # POST /decay


def main():
    CATALOG_URL = "http://localhost:8080"
    WRITER_PORT = requests.get(f"{CATALOG_URL}/writer_port").json().get("writer_port", 8090)
    core = WriterCore(
        catalog_url=CATALOG_URL
    )
    core.start()

    conf = {"/": {"request.dispatch": cherrypy.dispatch.MethodDispatcher()}}
    cherrypy.tree.mount(Root(core), "/", conf)
    cherrypy.config.update({"server.socket_host": "0.0.0.0", "server.socket_port": WRITER_PORT})
    cherrypy.engine.start()
    cherrypy.engine.block()


if __name__ == "__main__":
    main()
