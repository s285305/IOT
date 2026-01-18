import requests
from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt
import json
import threading
from influxdb_client_3 import InfluxDBClient3
import sys
import os

# Add the parent directory (PROJECT) to the system path
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'MQTT')))
from mqtt_client import Client


class Dashboard(Client):
    def __init__(self, catalog_url):
        super().__init__(catalog_url, type='dashboard')
        self.app = Flask(__name__)
        self.port = requests.get(f"{catalog_url}/dashboard_port").json().get("dashboard_port", 8081)
        self.http_port = 0
        self.influx_host = ''
        self.influx_token = ''
        self.influx_db = ''
        self.catalog=catalog_url
        self.get_db_info()

        self.influx_conf = {"host": self.influx_host, "token": self.influx_token, "db": self.influx_db}

        self.influxclient = InfluxDBClient3(
            host=self.influx_conf["host"], 
            token=self.influx_conf["token"], 
            database=self.influx_conf["db"]
        )

        self.client.on_message = self.message
        
        self.alerts = [] # Internal storage for alerts

        #routes for the frontend
        self.app.add_url_rule('/', 'index', self.serve_index)
        #self.app.add_url_rule('/api/config', 'get_config', self.get_frontend_config) #to connect json via MQTT, i don't think i'll need it
        self.app.add_url_rule('/api/history/<pole_id>', 'get_history', self.get_pole_history) #'mounts'
        # Add a route so the Frontend can "pull" the new alerts
        self.app.add_url_rule('/api/alerts', 'get_alerts', self.get_alerts)
        self.app.add_url_rule('/api/poles', 'get_poles', self.get_poles_for_map)
    
    def get_db_info(self):
        try:
            self.http_port = requests.get(f"{self.catalog_url}/writer_port").json().get("writer_port", 8090)
            print(f"[*] InfluxDB HTTP Port: {self.http_port}")
            self.influx_host = requests.get(f"{self.catalog_url}/db_info").json().get("influx_host", "http://localhost:8181")
            print(f"[*] InfluxDB Host: {self.influx_host}")
            self.influx_token = requests.get(f"{self.catalog_url}/db_info").json().get("token", "")
            print(f"[*] InfluxDB Token: {self.influx_token}")
            self.influx_db = requests.get(f"{self.catalog_url}/db_info").json().get("db", "pole_measurements")
            print(f"[*] InfluxDB Database: {self.influx_db}")
        except Exception as e:
            print('Impossible GET db info, error: ', e)

    def serve_index(self):
        return render_template('index.html')
    
    def get_frontend_config(self):
        return jsonify({
            'broker':self.broker,
            'topics': self.topics
        })
    
    def run(self):
        self.app.run(port=self.port, debug=True)

    def message(self, client, userdata, msg):
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
        

