import time
import json
import requests
import paho.mqtt.client as mqtt

class SmartGateway:
    def __init__(self, gateway_id, catalog_url, local_broker_ip, zone):
        self.gateway_id = gateway_id
        self.catalog_url = catalog_url
        self.local_broker_ip = local_broker_ip
        self.zone = zone
        
        self.known_poles = []

        self.client_local = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, f"{self.gateway_id}_local_subscriber")
        self.client_central = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, f"{self.gateway_id}_central_publisher")
        
        self.central_broker_conf = None

    # --- 1. REGISTRAZIONE DEL GATEWAY ---
    def register_gateway(self):
        payload = {
            "gateway_id": self.gateway_id,
            "gateway_topic": self.gateway_id,
            "zone": self.zone,
            "ip_address": "192.168.1.10", # IP finto del gateway
            "port": 8080,
            "smart_poles": [] 
        }

        try:
            print(f"[*] Mi sto registrando al Catalog: {self.catalog_url}")
            response = requests.post(f"{self.catalog_url}/register", json=payload)
            
            if response.status_code == 200 or response.status_code == 201:
                print("[*] Registrazione OK!")
                
                # ORA FACCIO UNA GET PER SCARICARE I DETTAGLI DEL BROKER CENTRALE
                resp_broker = requests.get(f"{self.catalog_url}/broker")
                self.central_broker_conf = resp_broker.json()
                print(f"[*] Broker Centrale ottenuto: {self.central_broker_conf}")
                return True
            else:
                print(f"[!] Errore registrazione: {response.text}")
                return False
        except Exception as e:
            print(f"[!] Impossibile contattare il Catalog: {e}")
            return False

    # --- 2. LOGICA DI BRIDGE ---
    def on_local_message(self, client, userdata, msg):
        try:
            try:
                payload_str = msg.payload.decode('utf-8')
            except UnicodeDecodeError:
                return 
            try:
                data = json.loads(payload_str)
            except json.JSONDecodeError:
                return
            if not isinstance(data, dict):
                return

            pole_id = data.get('pole_id')
            msg_type = data.get('type', 'data') 

            if not pole_id: return

            # Gestione Configurazione
            if msg_type == 'config':
                if pole_id not in self.known_poles:
                    print(f"[+] Configurazione ricevuta da {pole_id}. Registro...")
                    self.register_new_pole(data)
                return 

            # Gestione Dati
            if pole_id in self.known_poles:
                original_topic = msg.topic
                central_topic = f"{self.gateway_id}/{original_topic}" #aggiorno il topic per il central broker
                print(f"-> Dati da {pole_id} >> Cloud ({central_topic})")
                self.client_central.publish(central_topic, payload_str, qos=1)  #pubblica il messaggio al broker centrale

        except Exception as e:
            print(f"[!] Errore imprevisto: {e}")
    def register_new_pole(self, pole_data):
        # Creo il JSON specifico per aggiungere il palo al Catalog   
        pole_structure = {
            "gateway_id": self.gateway_id, 
            "smart_poles": [
                {
                    "pole_id": pole_data['pole_id'],
                    "pole_topic": f"{self.gateway_id}/{pole_data['pole_id']}",
                    "sensors": pole_data.get('sensors', []) 
                }
            ]
        }
        
        # Invio aggiornamento al Catalog
        try:
            requests.post(f"{self.catalog_url}/register", json=pole_structure) #sto postando il nuovo palo per aggiornare il catalog
            self.known_poles.append(pole_data['pole_id']) # Aggiungo alla cache
            print(f"[v] Palo {pole_data['pole_id']} registrato con successo.")
        except Exception as e:
            print(f"[!] Errore registrazione palo: {e}")

    # --- 3. AVVIO DEL SISTEMA ---
    def start(self):
        # 1. Registrazione iniziale
        if not self.register_gateway():
            print("Chiusura: Impossibile registrarsi.")
            return

        # 2. Connessione al Broker Locale (Input)
        try:
            self.client_local.on_message = self.on_local_message
            self.client_local.connect(self.local_broker_ip, 1883)
            # Sottoscrizione a TUTTI i pali della zona A (es. A/+/data_tommaso)
            self.client_local.subscribe(f"{self.zone}/+/data_tommaso")
            self.client_local.loop_start() # Thread separato per ascoltare
            print(f"[*] Connesso al Broker Locale ({self.local_broker_ip})")
        except Exception as e:
            print(f"[!] Errore connessione Broker Locale: {e}")
            return

        # 3. Connessione al Broker Centrale (Output)
        try:
            cb_addr = self.central_broker_conf['address']
            cb_port = self.central_broker_conf['port']
            self.client_central.connect(cb_addr, cb_port)
            self.client_central.loop_start()
            print(f"[*] Connesso al Broker Centrale ({cb_addr})")
            print(self.central_broker_conf)
        except Exception as e:
            print(f"[!] Errore connessione Broker Centrale: {e}")
            return

        # Loop infinito per tenere vivo lo script
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nSpegnimento Gateway...")
            self.client_local.loop_stop()
            self.client_central.loop_stop()

if __name__ == "__main__":

    CATALOG_URL = "http://localhost:8080" 
    
    LOCAL_BROKER = "test.mosquitto.org" 

    ZONE="A"
    gw = SmartGateway("gateway1", CATALOG_URL, LOCAL_BROKER, ZONE)
    gw.start()