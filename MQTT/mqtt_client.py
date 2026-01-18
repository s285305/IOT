#sovraclasse mqttClient, cosa fa:
# 1. POST sua registrazione nel catalog 
# 2. GET info per connessione MQTT al central broker -> loop
# 3. callbacks, on_subscribe chiama PUT per aggiornare lsita topics
# 4. funzione PUT
# 5. funzione DELETE
import requests
import time
import paho.mqtt.client as mqtt
import threading
import json

class Client():
    def __init__(self, catalog_url, type=''):
        self.catalog_url = catalog_url
        self.client_id = ''
        self.broker = {}
        self.topics = []
        self.type = type

        # Get initial info and register
        self.get_connection_info()

        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id
        )

        self.client.on_connect = self.connect
        self.client.on_message = self.message
        self.client.on_disconnect = self.disconnect
        self.on_publish = self.publish

        self.updater_thread = threading.Thread(target=self.refresh_get, daemon=True)

    def register(self):
        data = {'type': self.type, 'id': self.client_id}
        try:
            r = requests.post(f'{self.catalog_url}/{self.type}', json=data)
            print('Registration status code: ', r.status_code)
        except Exception as e:
            print('Impossible registration, error: ', e)

    def get_connection_info(self):
        try:
            self.get_broker()
            self.get_topics()
            self.get_client_id()
        except Exception as e:
            print('GET connection info error: ', e)

    def get_broker(self):
        try:
            r = requests.get(f'{self.catalog_url}/central_broker').json()
            self.broker = r
            print('Broker info successfully obtained: ', r)
        except Exception as e:
            print('Impossibile GET broker info, error: ', e)

    def get_topics(self):
        try:
            r = requests.get(f'{self.catalog_url}/topic', params=[('type', self.type)]).json()
            self.topics = r
            print('Topics info successfully obtained: ', self.topics)
        except Exception as e:
            print('Impossibile GET topics, error', e)

    def get_client_id(self):
        try:
            r = requests.get(f'{self.catalog_url}/compute_id', params=[('type', self.type)]).json()
            self.client_id = r['id']
            print(f'Mqtt client obtained: ', self.client_id)
        except Exception as e:
            print('Impossible GET client id, error: ', e)

    def refresh_get(self):
        while True:
            time.sleep(300) # Increased to 5 minutes to be polite to the server
            print('Refreshing info from catalog...')
            try:
                self.get_connection_info()
            except Exception as e:
                print(f"Update failed: {e}")

    def connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connection status: {reason_code}")
        # Automatically subscribe to topics found in catalog upon connection
        for topic in self.topics:
            client.subscribe(f'{topic}/#')
            print(f"Subscribed to {topic}")

    def message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            data = json.loads(payload)
            print(f"Received data on {msg.topic}: {data}")
        except Exception as e:
            print('Error on mqtt message: ', e)

    def disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        print('Disconnection code: ', reason_code)

    def subscribe(self, topic, qos=0):
        if topic not in self.topics:
            try:
                self.client.subscribe(f'{topic}/#', qos)
                self.topics.append(topic)
                data = {'new_topics': self.topics}
                requests.put(f'{self.catalog_url}/topic', params=[('type', self.type)], json=data)
                print(f'Successfully subscribed to {topic}')
            except Exception as e:
                print('Impossible to subscribe, error: ', e)
        else:
            print(f"Already subscribed to topic {topic}")

    def unsubscribe(self, topic):
        if topic in self.topics:
            try:
                self.client.unsubscribe(topic)
                self.topics.remove(topic)
                data = {'new_topics': self.topics}
                requests.put(f'{self.catalog_url}/topic', params=[('type', self.type)], json=data)
                print(f'Successfully unsubscribed from {topic}')
            except Exception as e:
                print('Impossible to unsubscribe, error: ', e)
        else:
            print(f"Topic {topic} not found in subscription list.")
    
    def publish(self, client, userdata, mid, reason_code=None, properties=None):
        print(f"Message {mid} published successfully.")

    def start(self):
        # Use loop_start() so it doesn't block the main thread
        self.register()
        self.client.connect(self.broker['address'], int(self.broker['port']))
        self.client.loop_start() 
        self.updater_thread.start()
        print("MQTT Background loop started.")

# --- MAIN BLOCK ---
if __name__ == '__main__':
    mqtt_client = Client('http://localhost:8080', 'dashboard')
    mqtt_client.start()
    
    # Now these will actually run because start() is non-blocking
    time.sleep(2) # Wait for connection to establish
    mqtt_client.subscribe('ciao')
    
    time.sleep(5)
    mqtt_client.unsubscribe('ciao')

    # Keep the program alive manually
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        mqtt_client.client.loop_stop()