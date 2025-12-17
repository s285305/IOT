import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

# --- CONFIGURAZIONE ---
BROKER = "test.mosquitto.org"
PORT = 1883
POLE_ID = "palo2"
ZONA = "A"
TOPIC = f"{ZONA}/{POLE_ID}/data_tommaso" 

# Metadata (Posizione diversa)
POLE_METADATA = {
    "pole_id": POLE_ID,
    "type": "config",
    "location": {
        "latitude": 45.0710,
        "longitude": 7.6890
    },
    "sensors": [
        {"sensor_id": "temp_02", "sensor_type": "thermometer", "unit": "Celsius"},
        {"sensor_id": "hum_02", "sensor_type": "hygrometer", "unit": "%"},
        {"sensor_id": "tilt_02", "sensor_type": "accelerometer", "unit": "degrees", "threshold": 15}
    ]
}

def get_readings():
    """Genera dati INSTABILI per testare l'allarme"""
    return {
        "temperature": round(random.uniform(18.0, 22.0), 2),
        "humidity": int(random.uniform(50, 70)),
        "tilt": round(random.uniform(10.0, 20.0), 2) 
    }

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, f"{POLE_ID}_device")
    
    print(f"[*] Connessione al broker locale: {BROKER}...")
    try:
        client.connect(BROKER, PORT)
    except Exception as e:
        print(f"[!] Errore: {e}")
        return

    client.loop_start()

    # --- FASE 1: CONFIGURAZIONE ---
    print(f"[1] Invio configurazione per registrazione...")
    client.publish(TOPIC, json.dumps(POLE_METADATA)) #invio solo i metadati per la config al catalog
    time.sleep(2)

    # --- FASE 2: DATI ---
    try:
        while True:
            readings = get_readings()
            
            payload = {
                "pole_id": POLE_ID,
                "type": "data",
                "timestamp": datetime.now().isoformat(),
                "values": readings
            }
            
            client.publish(TOPIC, json.dumps(payload)) #publico i miei dati al gateway per backend analysis e database
            
            print(f"-> {POLE_ID}: Tilt {readings['tilt']}°")
            
            time.sleep(5)

    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()