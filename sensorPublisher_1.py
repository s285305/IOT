import time
import paho.mqtt.client as mqtt
import json
import random
import threading # Aggiunto per gestire il loop senza bloccare MQTT


# Limitare intervallo publish

class PolePublisher:
    # Prende la configurazione dal file
    config = json.load(open("config.json"))
    
    broker = config["broker"]["address"]
    port = config["broker"]["port"]
    regions = config["regions"] 
    topic = config["topic"]
    counter = 0

    def __init__(self, coordinates):
        # Caratteristiche del palo
        self.interval = PolePublisher.config["interval"]
        self.stopped = False
        self.sensors = PolePublisher.config["sensors"]
        self.lat = coordinates['lat']
        self.long = coordinates['long']
        self.region = self.get_region(self.lat, self.long, PolePublisher.regions)
        self.tilt = round(random.uniform(0.0, 2.0), 2)  # quasi dritto all'inizio

        # ID unico
        self.client_id = f"PolePublisher_{PolePublisher.counter}"
        PolePublisher.counter += 1
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id,
        )
        self.this_topic = f"{PolePublisher.topic}/{self.region}/{self.client_id}"
        self.cmd_base = PolePublisher.config.get("cmd_topic", "poleCmd")
        self.cmd_topic = f"{self.cmd_base}/{self.client_id}"
        self.client.on_message = self.on_cmd_message

        # Registrazione callback
        self.client.on_connect = self.My_on_connect
        self.client.on_publish = self.My_on_publish

        # Connessione al broker
        self.client.connect(PolePublisher.broker, PolePublisher.port)
        self.client.loop_start()

    def generate_measurements(self):
        """Metodo start originale rinominato per chiarezza"""
        # ogni ciclo: o resta uguale o aumenta di poco
        inc = random.choice([0.0, 0.0, 0.01, 0.02, 0.05])  # più spesso 0, a volte cresce
        noise = random.uniform(-0.02, 0.02)               # piccolo rumore
        self.tilt = max(self.tilt, self.tilt + inc + noise)  
        tilt_value = round(self.tilt, 2)
        if not self.stopped:                
            return {
                "id": self.client_id,
                "timestamp": int(time.time()),
                "temperature": round(random.uniform(20.0, 25.0), 2),
                "humidity": int(random.uniform(40, 60)),
                "tilt": tilt_value
            }
    
    def run(self):
        """Avvia la sequenza Configurazione + Misure in un thread separato"""
        thread = threading.Thread(target=self._logic_loop)
        thread.daemon = True
        thread.start()

    def _logic_loop(self):
        """Gestisce l'invio sequenziale senza bloccare il thread di rete"""
        # 1. Invia il messaggio di CONFIGURAZIONE (Primo messaggio)
        config_msg = {
            "id": self.client_id,
            "lat": self.lat,
            "long": self.long,
            "region": self.region,
            "topic": self.this_topic,
            "sensors": self.sensors,
            "message": "config"
        }
        self.client.publish(self.this_topic, json.dumps(config_msg), qos=1)
        print(f"[*] Configurazione inviata per {self.client_id}")

        # Aspetta un secondo per dare tempo al Gateway di registrarsi
        time.sleep(1)

        # 2. Invia le MISURE continuamente
        print(f"[*] Inizio invio misure per {self.client_id}...")
        while not self.stopped:
            measurements = self.generate_measurements()
            if self.stopped:
                break
            self.client.publish(self.this_topic, json.dumps(measurements), qos=0)
            print(f"Published measurements from {self.client_id} to {self.this_topic} in port {PolePublisher.port}")
            time.sleep(self.interval)

    def My_on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected to broker with code: {reason_code}")
        # subscribe ai comandi
        client.subscribe(self.cmd_topic, qos=1)
        print(f"[*] Subscribed to commands: {self.cmd_topic}")

    def on_cmd_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return

        cmd = data.get("cmd")
        if cmd == "deactivate":
            print(f"[!] Command deactivate received for {self.client_id}")
            self.stopped = True
            # opzionale: chiusura pulita
            self.client.loop_stop()
            self.client.disconnect()

    def My_on_publish(self, client, userdata, mid, reason_code, properties):
        # Lasciamo vuoto o solo un log per evitare loop ricorsivi infiniti
        pass

    def stop(self):
        self.stopped = True

    def finalize(self):
        self.client.loop_stop()
        self.client.disconnect()

    def get_region(self, lat, long, regions):
        for region_name, bounds in regions.items():
            if (
                bounds["minLat"] <= lat <= bounds["maxLat"] and
                bounds["minLon"] <= long <= bounds["maxLon"]
            ):
                return region_name
        return None

if __name__ == "__main__":
    # Creazione istanze
    sensor1 = PolePublisher({'lat': 45.0, 'long': 7.0})
    sensor2 = PolePublisher({'lat': 46.0, 'long': 10.0})
    sensor3 = PolePublisher({'lat': 45.5, 'long': 9.0})
    sensor4 = PolePublisher({'lat': 44.5, 'long': 9.0})
    # sensor6 = PolePublisher({'lat': 45.0, 'long': 7.0}) 

    # Avvio dei pali: manderanno config e poi misure da soli
    sensor1.run()
    sensor2.run()
    sensor3.run()
    sensor4.run()
    # sensor6.run()

    # Mantiene il processo attivo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sensor1.finalize()
        sensor2.finalize()
        sensor3.finalize()
        sensor4.finalize()