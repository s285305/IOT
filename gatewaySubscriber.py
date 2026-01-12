import json
import paho.mqtt.client as mqtt
import requests
import threading
import time

class GatewaySubscriber:
    counter = 0
    known_gateways = []
    def __init__(self, coordinates, catalog_url):

        self.catalog_url = catalog_url
        regions = requests.get(f"{self.catalog_url}/regions").json()
        self.coordinates = coordinates
        self.region = self.get_region(coordinates['lat'], coordinates['long'], regions)      
        self.central_broker_conf= None
        self.local_broker_conf = None
        #unique ID
        self.client_id = "GatewaySubscriber_" + GatewaySubscriber.counter.__str__()
        GatewaySubscriber.counter += 1
        #storing topics it is subscribed to, it is always subscribed to its region
        topic = "poleData/"+self.region+"/#"
        self.topics = [topic]
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2, 
            client_id=self.client_id)      
        self.client_central = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,client_id=self.client_id+"_central") 
        # register callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_local_message
        self.client_central.on_publish = self._on_publish        

        self.known_poles = []  #cache dei pali già registrati
    
        cb_info=self.get_broker_central()
        lb_info=self.get_broker_local()

    def _on_publish(self, client, userdata, mid, reason_code, properties):
        print(f"Message {mid} published.")

    def get_region(self, lat, long, regions):

        for region_name, bounds in regions.items():
            if (
                bounds["minLat"] <= lat <= bounds["maxLat"] and
                bounds["minLon"] <= long <= bounds["maxLon"]
            ):
                return region_name
            

        return 'None'

    def get_broker_central(self):
        resp_broker = requests.get(f"{self.catalog_url}/central_broker")
        self.central_broker_conf = resp_broker.json()
        print(f"[*] Broker Centrale ottenuto: {self.central_broker_conf}")
        return self.central_broker_conf
    
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
            return True  # fail-open
        
    def send_deactivate_cmd(self, pole_id: str):
        cmd_base = self.topics['cmd_topic']  
        topic = f"{cmd_base}/{pole_id}"
        payload = json.dumps({"cmd": "deactivate", "ts": time.time()})
        # pubblica sul broker locale
        self.client.publish(topic, payload, qos=1, retain=False)
        print(f"[!] Sent deactivate to {topic}")


    
    #registering a new pole in the catalog with configuration data, da usare solo quando riceve messaggio da palo sconosciuto
    def register_new_pole(self, pole_data):        
            payload = pole_data
            payload['gateway_id'] = self.client_id  #associo palo a questo gateway
            
            try:
                resp = requests.post(f"{self.catalog_url}/pole", json=payload, timeout=5)
                if resp.status_code in (200, 201):
                    self.known_poles.append(payload["id"])
                    print(f"[v] Palo {payload['id']} registrato con successo.")
                    print("Known poles test funzione registra palo:",self.known_poles)

                else:
                    print(f"[!] Errore registrazione palo ({resp.status_code}): {resp.text}")
            except Exception as e:
                print(f"[!] Errore registrazione palo: {e}")
                #aggiungere logica per invio dati a database

    # def on_local_message(self, client, userdata, msg):
    #     payload_str = msg.payload.decode('utf-8')
    #     data = json.loads(payload_str)
    #     pole_id = data.get('id')
    #     msg_type = data.get('message', 'data')

    #     print('Siamo dentro local message, pole id', pole_id)

    #     if msg_type == 'config' and pole_id not in self.known_poles:
    #         print(f"[+] Configurazione ricevuta da {pole_id}. Registro...")
            
    #         # Start a new thread so we don't block the MQTT loop
    #         t = threading.Thread(target=self.register_new_pole, args=(data,))
    #         t.start()

    #         # self.register_new_pole(data) 
    #         # print("Known poles:",self.known_poles)

    #     # Gestione Dati
    #     elif pole_id in self.known_poles:
    #             original_topic = data.get('topic', 'poleData')
    #             central_topic = f"{self.client_id}/{original_topic}" #aggiorno il topic per il central broker
    #             print(f"-> Dati da {pole_id} >> Cloud ({central_topic})")
    #             self.client_central.publish(central_topic, payload_str, qos=1)  #pubblica il messaggio al broker centrale

    #GEMINI
    def on_local_message(self, client, userdata, msg):
        print("DEBUG: dentro on_local_message", msg.topic)
        try:
            payload_str = msg.payload.decode('utf-8')
            data = json.loads(payload_str)
            pole_id = data.get('id')
            msg_type = data.get('message', 'data')

            print(f'DEBUG: Messaggio ricevuto da {pole_id} ({msg_type})')

            if msg_type == "config":
                if not self.get_pole_active(pole_id):
                    print(f"[!] {pole_id} inactive in catalog -> sending deactivate")
                    self.send_deactivate_cmd(pole_id)
                    return

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

                if self.client_central.is_connected():
                    central_topic = f"{data.get('topic', 'poleData')}/{self.client_id}"
                    print(f"-> Forwarding data from {pole_id} to Cloud ({central_topic})")
                    self.client_central.publish(central_topic, payload_str, qos=1)
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
        if payload["zone"] in GatewaySubscriber.known_gateways:
            print(f"[*] Gateway {payload['zone']} possiede già un gateway.")
            return
        else:
            GatewaySubscriber.known_gateways.append(payload["zone"])
            try:
                print(f"[*] Mi sto registrando al Catalog: {self.catalog_url}")
                response = requests.post(f"{self.catalog_url}/gateway", json=payload)           
                if response.status_code == 200 or response.status_code == 201:
                    print("[*] Registrazione OK!")
                    return True
                else:
                    print(f"[!] Errore registrazione: {response.text}")
                    return False
            except Exception as e:
                print(f"[!] Impossibile contattare il Catalog: {e}")
                return False

    #def start(self):
        if not self.register_gateway():
            print("Chiusura: Impossibile registrarsi.")
            return

        print("Vado a local message")
        #self.client.on_message = self.on_local_message
        self.client.connect(self.local_broker_conf["address"], self.local_broker_conf["port"])
        self.client.loop_start()

        # CENTRAL
        self.client_central.connect(self.central_broker_conf["address"], self.central_broker_conf["port"])
        self.client_central.loop_start()
    
    #GEMINI
    def start(self):
        if not self.register_gateway():
            print("Chiusura: Impossibile registrarsi.")
            return

        # 1. Setup Central Client FIRST (with its own connect log)
        self.client_central.on_connect = lambda c, u, f, rc, p: print(f"[*] Cloud: Connesso (RC: {rc})")
        
        print("[*] Avvio loop di rete...")
        self.client.loop_start()
        self.client_central.loop_start() # Start the loop BEFORE connecting to avoid publish-hangs

        try:
            print(f"[*] Connessione Local ({self.local_broker_conf['address']})...")
            self.client.connect(self.local_broker_conf["address"], self.local_broker_conf["port"])
            
            print(f"[*] Connessione Central ({self.central_broker_conf['address']})...")
            self.client_central.connect(self.central_broker_conf["address"], self.central_broker_conf["port"])
        except Exception as e:
            print(f"[!] Errore connessione broker: {e}")
        

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected with reason code {reason_code}")
        print("Successfully connected to broker")

        # si riscrive a tutti gli argomenti a ogni riconnessione, così non li perde
        for topic in self.topics:
            self.client.subscribe(topic)

    def on_disconnect(self, client, userdata, *args):
        print(f"Disconnected with reason code {args[0]}")

    def subscribe(self, topic, qos=0):
        if topic not in self.topics:
            self.client.subscribe(topic, qos)
            self.topics.append(topic)
        else:
            print(f"Already subscribed to topic {topic}")

    def unsubscribe(self, topic):
        if topic in self.topics:
            self.client.unsubscribe(topic)
            self.topics.remove(topic)
        else:
            print(f"Not subscribed to topic {topic}")

    def finalize(self):
        print("Finalizing subscriber...")
        self.client.loop_stop()
        self.client.disconnect()


if __name__ == "__main__":
    import time

    gateway1 = GatewaySubscriber({'lat': 45.0, 'long': 7.0}, "http://localhost:8080")
    gateway1.start()
    gateway2 = GatewaySubscriber({'lat': 46.0, 'long': 10.0}, "http://localhost:8080")
    gateway2.start()
    gateway6 = GatewaySubscriber({'lat': 45.0, 'long': 7.0}, "http://localhost:8080") 
    gateway6.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSpegnimento Gateway...")
        gateway1.client.loop_stop()



