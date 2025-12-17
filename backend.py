import paho.mqtt.client as mqtt
import requests
import json
import time

class BackendAnalytics:
    def __init__(self, client_id, catalog_url, broker_address, broker_port):
        self.client_id = client_id
        self.catalog_url = catalog_url
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id)

        self.thresholds_cache = {}
        self.broker_address = broker_address
        self.broker_port = broker_port

    def update_thresholds_from_catalog(self):
        """
        Fa una GET al Resource Catalog per sapere quali sono i limiti.
        """
        try:
            print("[*] Aggiornamento soglie dal Catalog...")
            response = requests.get(self.catalog_url)
            if response.status_code == 200:
                data = response.json()
                self._parse_catalog_data(data)
                print(f"[*] Soglie aggiornate: {len(self.thresholds_cache)} pali configurati.")
            else:
                print(f"[!] Errore Catalog: {response.status_code}")
        except Exception as e:
            print(f"[!] Impossibile contattare Catalog: {e}")

    def _parse_catalog_data(self, catalog_data):
        """Estrae le soglie dal JSON complesso del Catalog"""
        # Pulisce la cache vecchia
        self.thresholds_cache = {}
        
        gateways = catalog_data.get("gateways", [])
        for gw in gateways:
            gw_id = gw.get("gateway_id")
            gw_zone = gw.get("zone")  
            for pole in gw.get("smart_poles", []):
                pole_id = pole.get("pole_id")
                # Chiave univoca per trovare il palo: "gateway1/A/palo1"
                key = f"{gw_id}/{gw_zone}/{pole_id}"
                self.thresholds_cache[key] = {}
                
                for sensor in pole.get("sensors", []):
                    if "threshold" in sensor:
                        s_type = sensor["sensor_type"] 
                        limit = sensor["threshold"]
                        self.thresholds_cache[key][s_type] = limit


    def on_message(self, client, userdata, msg):
        """Analizza i dati in arrivo dal Broker Centrale"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
        
            # print(f"\n[DEBUG] Topic ricevuto: {topic}")
            # Il topic è tipo: gateway1/palo1/data
            parts = topic.split('/')
    
            if len(parts) >= 3:
                gateway_id = parts[0]
                zone = parts[1]
                pole_id = parts[2]
            else:
                print(f"[!] Topic inaspettato: {topic}")
                return

            device_key = f"{gateway_id}/{zone}/{pole_id}"
            
            # print(f"[DEBUG] Chiave costruita: '{device_key}'")
            # print(f"[DEBUG] Chiavi disponibili in cache: {list(self.thresholds_cache.keys())}")
            
            if device_key not in self.thresholds_cache:
                print(f"[!] Chiave '{device_key}' NON trovata in cache. Aggiorno...")
                self.update_thresholds_from_catalog()

            # Nota: Qui controlliamo di nuovo dopo l'aggiornamento
            if device_key in self.thresholds_cache:
                limits = self.thresholds_cache[device_key]
                values = payload.get("values", {})
                current_tilt = values.get("tilt")
                tilt_limit = limits.get("accelerometer") 
                
                if current_tilt is not None and tilt_limit is not None:
                    if float(current_tilt) > float(tilt_limit):
                        print(f"!!! ALLARME RILEVATO !!! {device_key}: Tilt {current_tilt}° > Limite {tilt_limit}°")
                        self.publish_alarm(gateway_id, zone, pole_id, "tilt", current_tilt)
                    else:
                        print(f"[OK] {device_key}: Tilt {current_tilt}° (Limite {tilt_limit}°)")
            else:
                 print(f"[!!!] ANCORA ERRORE: Anche dopo aggiornamento, '{device_key}' non esiste nel Catalog.")

        except Exception as e:
            print(f"[!] Errore analisi messaggio: {e}")

    def publish_alarm(self, gw_id,zone, pole_id, alert_type, value, qos=1):
        """Pubblica l'allarme sul Broker Centrale"""
        alarm_topic = f"{gw_id}/{zone}/{pole_id}/alarms"
        alarm_payload = {
            "alert_type": alert_type,
            "value": value,
            "msg": "DANGER: Threshold exceeded",
            "timestamp": time.time()
        }
        self.client.publish(alarm_topic, json.dumps(alarm_payload), qos=qos)
        print(f"-> Allarme inviato su: {alarm_topic}")

    def start(self):

        self.update_thresholds_from_catalog()

        self.client.on_message = self.on_message
        self.client.connect(self.broker_address, self.broker_port)
        
        self.client.subscribe("+/+/+/data_tommaso")
        
        print(f"[*] Backend Analytics avviato. In ascolto su {self.broker_address}...")
        self.client.loop_forever()

if __name__ == "__main__":

    CATALOG_URL = "http://localhost:8080"
    
    BROKER = "broker.hivemq.com"
    
    analytics = BackendAnalytics("backend_analytics_service", CATALOG_URL, BROKER, 1883)
    analytics.start()