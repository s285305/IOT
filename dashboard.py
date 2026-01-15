import requests
from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt
import json
import threading
from influxdb_client_3 import InfluxDBClient3

class Dashboard():
    counter = 0

    def __init__(self, catalog, port=8081):
        
        self.app = Flask(__name__)
        self.client_id = 'Dashboard_'+str(Dashboard.counter)
        self.catalog = catalog
        self.port = port
        self.http_port = requests.get(f"{catalog}/db_info").json().get("writer_port", 8090)
        print(f"[*] InfluxDB HTTP Port: {self.http_port}")
        influx_host = requests.get(f"{catalog}/db_info").json().get("influx_host", "http://localhost:8181")
        print(f"[*] InfluxDB Host: {influx_host}")
        influx_token = requests.get(f"{catalog}/db_info").json().get("token", "")
        print(f"[*] InfluxDB Token: {influx_token}")
        influx_db = requests.get(f"{catalog}/db_info").json().get("db", "pole_measurements")
        print(f"[*] InfluxDB Database: {influx_db}")

        self.influx_conf = {"host": influx_host, "token": influx_token, "db": influx_db}

        self.influxclient = InfluxDBClient3(
            host=self.influx_conf["host"], 
            token=self.influx_conf["token"], 
            database=self.influx_conf["db"]
        )

        self.broker={}
        self.topics=[]

        #1 get config from catalog and register itself
        self.get_config()
        self.register()

        self.alerts = [] # Internal storage for alerts

        #routes for the frontend
        self.app.add_url_rule('/', 'index', self.serve_index)
        #self.app.add_url_rule('/api/config', 'get_config', self.get_frontend_config) #to connect json via MQTT, i don't think i'll need it
        self.app.add_url_rule('/api/history/<pole_id>', 'get_history', self.get_pole_history) #'mounts'
        # Add a route so the Frontend can "pull" the new alerts
        self.app.add_url_rule('/api/alerts', 'get_alerts', self.get_alerts)
        self.app.add_url_rule('/api/poles', 'get_poles', self.get_poles_for_map)

        #MQTT connection setup
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id
        )

        # register callbacks
        self.client.on_connect = self.connect
        self.client.on_message = self.on_message

        self.client.connect(self.broker['address'], self.broker['port'])
        self.client.loop_start()

        #in case it registered to more than one topic
        for topic in self.topics:
            self.client.subscribe(topic, qos=1)

        Dashboard.counter +=1 #se ci fosse più di una
    
    def register(self):
        payload = {
            "id":self.client_id
        }
        try:
            r = requests.post(f"{self.catalog}/dashboard", json=payload)
            r.raise_for_status()
            print("[*] Registrazione come Dashboard riuscita")
            return r 
        except Exception as e:
            print(f"Error connecting to Catalog: {e}")
    
    def get_config(self):
        try:
            self.broker['port'] = int(requests.get(f'{self.catalog}/central_broker').json()['port'])
            self.broker['address'] = requests.get(f'{self.catalog}/central_broker').json()['address']
            
            topic = requests.get(f'{self.catalog}/topic').json()['dashboard']
            self.topics.append(topic)

            print(f'Broker port {self.broker["port"]}, Broker address {self.broker["address"]}')
            for topic in self.topics:
                print(f'Topic: {topic}')

            

            return self.broker, self.topics
        except Exception as e:
            print(f"Error connecting to Catalog: {e}")

    def serve_index(self):
        return render_template('index.html')
    
    def get_frontend_config(self):
        return jsonify({
            'broker':self.broker,
            'topics': self.topics
        })
    
    def run(self):
        self.app.run(port=self.port, debug=True)
    
    #my methods for the callbacks
    def connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connection status: {str(reason_code)}")

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            # We assume data has {'pole_id': 'P01', 'alert': 'Tilt...'}
            self.alerts.append(data) 
            print(f"Alert received: {data}")
        except Exception as e:
            print(f"Error on message: {e}")

    def get_pole_history(self, pole_id):
        # SQL-like query for InfluxDB 3.0
        query = f"""
            SELECT time, temperature, humidity, decay, tilt
            FROM pole_measurements 
            WHERE pole_id = '{pole_id}' 
            AND time >= now() - interval '60 minutes'
            ORDER BY time DESC
        """
        # Convert the table result to a list of dictionaries (JSON friendly)
        table = self.influxclient.query(query)
        df = table.to_pandas()
        return jsonify(df.to_dict(orient='records'))

    def get_alerts(self):
        # This returns the current list and then clears it
        temp_alerts = list(self.alerts)
        self.alerts = [] 
        return jsonify(temp_alerts)

    # def old_get_poles_for_map(self):
    #     try:
    #         # 1. Get static info from your Catalog (The 'gateways' list)
    #         # Your catalog returns the full list at /gateways
    #         gateways = requests.get(f"{self.catalog}/gateways").json()

    #         final_poles = []
            
    #         # Map for quick lookup: { 'pole_id': {lat, lon, gateway_id} }
    #         static_poles = {}
    #         for gw in gateways:
    #             gw_id = gw.get("gateway_id")
    #             for p in gw.get("smart_poles", []):
    #                 # Only map active poles
    #                 if p.get("active", True):
    #                     static_poles[p["id"]] = {
    #                         "lat": p.get("lat"),
    #                         "lon": p.get("long"),
    #                         "gateway_id": gw_id
    #                     }
    #                     final_poles.append(p)

    #         # 2. Get latest values from InfluxDB for all poles
    #         # We use last() to get the most recent entry for each field
    #         # query = """
    #         #     SELECT last(temperature) as temp, 
    #         #            last(humidity) as hum, 
    #         #            last(decay) as dec, 
    #         #            last(tilt) as tlt
    #         #     FROM pole_measurements 
    #         #     GROUP BY pole_id
    #         # """
    #         # table = self.influx_client.query(query)
    #         # df = table.to_pandas()

    #         # # 3. Merge Catalog (Locations) + Influx (Live Sensors)
    #         # final_poles = []
    #         # for _, row in df.iterrows():
    #         #     pid = row['pole_id']
                
    #         #     # Only include if the pole exists in the Catalog
    #         #     if pid in static_poles:
    #         #         final_poles.append({
    #         #             "id": pid,
    #         #             "lat": static_poles[pid]["lat"],
    #         #             "lon": static_poles[pid]["lon"],
    #         #             "gateway_id": static_poles[pid]["gateway_id"],
    #         #             "temperature": row['temp'],
    #         #             "humidity": row['hum'],
    #         #             "decay": row['dec'],
    #         #             "tilt": row['tlt']
    #         #         })

    #         return jsonify(final_poles)

    #     except Exception as e:
    #         print(f"Error building map data: {e}")
    #         return jsonify([]), 500

    def get_poles_for_map(self):
        try:
            # Request data from your Catalog
            response = requests.get(f"{self.catalog}/gateways")
            gateways = response.json()
            
            final_poles = []
            
            # We need to dive into each gateway to find the smart_poles list
            for gw in gateways:
                gw_id = gw.get("gateway_id")
                for p in gw.get("smart_poles", []):
                    # We map the Catalog fields to what the Javascript expects
                    if p.get("active") is True:
                        final_poles.append({
                            "id": p.get("id"),
                            "lat": p.get("lat"),
                            "lon": p.get("long"),  # Leaflet usually wants 'lon'
                            "region": p.get("region"),
                            "gateway": gw_id,
                            "temperature": "N/A",  # Placeholder until Influx is back
                            "humidity": "N/A"
                        })
            
            print(f"[*] Found {len(final_poles)} poles in Catalog")
            return jsonify(final_poles)
        except Exception as e:
            print(f"[!] Catalog Error: {e}")
            return jsonify([])
    
if __name__ == '__main__':
    d = Dashboard("http://localhost:8080")
    d.run()
        

