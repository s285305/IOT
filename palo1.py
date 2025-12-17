import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

# --- CONFIGURAZIONE ---
BROKER = "test.mosquitto.org" 
PORT = 1883
POLE_ID = "palo1"
ZONA = "A"
TOPIC = f"{ZONA}/{POLE_ID}/data_tommaso" 

# Metadata (inviati solo all'avvio per la registrazione)
POLE_METADATA = {
    "pole_id": POLE_ID,
    "type": "config",  # Flag per dire al Gateway: "Questa è una registrazione"
    "location": {
        "latitude": 45.0703,
        "longitude": 7.6869
    },
    "sensors": [

        {"sensor_id": "temp_01", "sensor_type": "thermometer", "unit": "Celsius"},
        {"sensor_id": "hum_01", "sensor_type": "hygrometer", "unit": "%"},
        {"sensor_id": "tilt_01", "sensor_type": "accelerometer", "unit": "degrees", "threshold": 15}
    ]
}

def get_readings():
    """Genera dati stabili (nessun allarme)"""
    return {
        "temperature": round(random.uniform(20.0, 25.0), 2),
        "humidity": int(random.uniform(40, 60)),
        "tilt": round(random.uniform(0.0, 2.0), 2) 
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

    # --- FASE 1: INVIO CONFIGURAZIONE (BOOT) ---
    print(f"[1] Invio configurazione (Auto-provisioning)...")
    client.publish(TOPIC, json.dumps(POLE_METADATA)) #invio solo i metadati per la config al catalog
    time.sleep(2) # Diamo tempo al Gateway di elaborare

    # --- FASE 2: LOOP DATI (RUNTIME) ---
    print(f"[2] Inizio invio dati sensori...")
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
            print(f"-> {POLE_ID}: Temp {readings['temperature']}°C, Hum {readings['humidity']}%, Tilt {readings['tilt']}°")
            
            time.sleep(5) # Invio ogni 5 secondi

    except KeyboardInterrupt:
        print("Spegnimento...")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()