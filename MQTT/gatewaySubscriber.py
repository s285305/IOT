import json
import paho.mqtt.client as mqtt
import requests
import threading
import time
from mqtt_client import Client

class GatewaySubscriber(Client):
    def __init__(self, coordinates, catalog_url):
        self.coordinates = coordinates
        super().__init__( catalog_url, type='gateway')
        self.catalog_url = catalog_url
        regions = requests.get(f"{self.catalog_url}/regions").json()
        self.region = self.get_region(coordinates['lat'], coordinates['long'], regions)      
        self.local_broker_conf = self.get_broker_local()
        self.central_broker_conf = self.broker  # from parent class
        #unique ID
        self.client_id = self.get_client_id()
        self.client_local = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2, 
            client_id=self.client_id)        
        self.known_poles = set()  #cache dei pali già registrati

    def get_client_id(self):
        try:
            r = requests.get(f"{self.catalog_url}/compute_id?type=gateway&lat={self.coordinates['lat']}&lon={self.coordinates['long']}").json()
            self.client_id = r['id']
            print(f'Mqtt client obtained: ', self.client_id)
            return self.client_id
        except Exception as e:
            print('Impossible GET client id, error: ', e)

    def get_region(self, lat, long, regions):

        for region_name, bounds in regions.items():
            if (
                bounds["minLat"] <= lat <= bounds["maxLat"] and
                bounds["minLon"] <= long <= bounds["maxLon"]
            ):
                return region_name
        return 'None'
    
    def get_broker_local(self):
        resp_broker = requests.get(f"{self.catalog_url}/local_broker")
        self.local_broker_conf = resp_broker.json()
        print(f"[*] Broker Locale ottenuto: {self.local_broker_conf}")
        return self.local_broker_conf
    
    def get_pole_active(self, pole_id: str) -> bool:
        try:
            r = requests.get(f"{self.catalog_url}/pole_status/{pole_id}", timeout=2)
            if r.status_code != 200:
                return True
            return bool(r.json().get("active", True))
        except Exception:
            return True # fail-open
        
    def send_deactivate_cmd(self, pole_id: str):
        cmd_base = requests.get(f"{self.catalog_url}/topic?type=cmd_topic").json()
        topic = f"{cmd_base}/{pole_id}"
        payload = json.dumps({"cmd": "deactivate", "ts": time.time()})
        # pubblica sul broker locale
        self.client_local.publish(topic, payload, qos=1, retain=False)
        print(f"[!] Sent deactivate to {topic}")

    def delete_pole_from_catalog(self, pole_id: str):
        try:
            url = f"{self.catalog_url}/pole/{self.client_id}/{pole_id}"
            r = requests.delete(url, timeout=5)
            print(f"[*] DELETE {url} -> {r.status_code} {r.text}")
            # keep local cache consistent
            if pole_id in self.known_poles:
                self.known_poles.remove(pole_id)
        except Exception as e:
            print(f"[!] Errore delete pole dal catalog: {e}")

    def on_local_connect(self, client, userdata, flags, reason_code, properties):
        print(f"[*] Local: Connesso (RC: {reason_code})")
        client.subscribe(f"poleData/{self.region}/#", qos=1)

    
    #registering a new pole in the catalog with configuration data, da usare solo quando riceve messaggio da palo sconosciuto
    def register_new_pole(self, pole_data):        
            payload = pole_data
            payload['gateway_id'] = self.client_id  #associo palo a questo gateway
            
            try:
                resp = requests.post(f"{self.catalog_url}/pole", json=payload, timeout=5)
                if resp.status_code in (200, 201):
                    self.known_poles.add(payload["id"])
                    print(f"[v] Palo {payload['id']} registrato con successo.")
                    print("Known poles test funzione registra palo:",self.known_poles)

                else:
                    print(f"[!] Errore registrazione palo ({resp.status_code}): {resp.text}")
            except Exception as e:
                print(f"[!] Errore registrazione palo: {e}")

    def on_local_message(self, client, userdata, msg):
        print("DEBUG: dentro on_local_message", msg.topic)
        try:
            payload_str = msg.payload.decode('utf-8')
            data = json.loads(payload_str)
            pole_id = data.get('id')
            msg_type = data.get('message', 'data')

            print(f'DEBUG: Messaggio ricevuto da {pole_id} ({msg_type})')

            if msg_type in ("unregister", "offline"):
                print(f"[*] Request to remove pole {pole_id} from catalog")
                self.delete_pole_from_catalog(pole_id)
                return

            if msg_type == "config":
                if pole_id not in self.known_poles:
                    print(f"[+] Registro nuovo palo: {pole_id}")
                    t = threading.Thread(target=self.register_new_pole, args=(data,))
                    t.start()
                return

            elif pole_id in self.known_poles:
                print("DEBUG entro in ramo dati")

                if not self.get_pole_active(pole_id):
                    self.send_deactivate_cmd(pole_id)
                    return

                if self.client.is_connected():
                    central_topic = f"{data.get('topic', 'poleData')}/{self.client_id}"
                    print(f"-> Forwarding data from {pole_id} to Cloud ({central_topic}) port {self.central_broker_conf['port']}")
                    self.client.publish(central_topic, payload_str, qos=1)
                else:
                    print(f"[!] Cloud non connesso, messaggio da {pole_id} perso.")
        except Exception as e:
            print(f"[!] Errore gestione messaggio locale: {e}")


    def register_gateway(self):

        payload = {
            "gateway_id": self.client_id,
            "gateway_topic": self.topics,
            "zone": self.region,
            "smart_poles": [] 
        }
        try:
            print(f"[*] Mi sto registrando al Catalog: {self.catalog_url}")
            response = requests.post(f"{self.catalog_url}/{self.type}", json=payload)           
            if response.status_code == 200 or response.status_code == 201:
                print("[*] Registrazione OK!")
                return True
            else:
                print(f"[!] Errore registrazione: {response.text}")
                return False
        except Exception as e:
                print(f"[!] Impossibile contattare il Catalog: {e}")
                return False
    
    #GEMINI
    def start(self):
        if not self.register_gateway():
            print("Chiusura: Impossibile registrarsi.")
            return

        # 1. Setup Central Client FIRST (with its own connect log)
        self.client.on_connect = lambda c, u, f, rc, p: print(f"[*] Cloud: Connesso (RC: {rc})")
        
        print("[*] Avvio loop di rete...")
        self.client.loop_start() # Start the loop BEFORE connecting to avoid publish-hangs

        try:
            print(f"[*] Connessione Local ({self.local_broker_conf['address']})...")
            self.client_local.on_connect = self.on_local_connect
            self.client_local.on_message = self.on_local_message
            self.client_local.connect(self.local_broker_conf["address"], self.local_broker_conf["port"])
            self.client_local.loop_start()

            print(f"[*] Connessione Central ({self.central_broker_conf['address']}) {self.central_broker_conf['port']}...")
            self.client.on_connect = lambda c,u,f,rc,p: print(f"[*] Cloud: Connesso (RC: {rc})")
            self.client.connect(self.central_broker_conf["address"], self.central_broker_conf["port"])
            self.client.loop_start()

        except Exception as e:
            print(f"[!] Errore connessione broker: {e}")

    def finalize(self):
        print("Finalizing subscriber...")
        self.client_local.loop_stop()
        self.client_local.disconnect()
        self.client.loop_stop()
        self.client.disconnect()


if __name__ == "__main__":
    import time

    gateway1 = GatewaySubscriber({'lat': 45.0, 'long': 7.0}, "http://localhost:8080")
    gateway1.start()
    gateway2 = GatewaySubscriber({'lat': 46.0, 'long': 10.0}, "http://localhost:8080")
    gateway2.start()
    # gateway6 = GatewaySubscriber({'lat': 45.0, 'long': 7.0}, "http://localhost:8080") 
    # gateway6.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSpegnimento Gateway...")
        gateway1.client.loop_stop()
