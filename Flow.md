# Complete description of the system

The proposed IoT platform for Smart Poles follows the microservices designing pattern. It also exploits two communication paradigms: i) publish/subscribe based on MQTT protocol and ii) request/response based on REST Web Services.

In this context, eight actors have been identified and introduced in the following:

* The **Message Broker** provides an asynchronous communication based on the publish/subscribe approach. It exploits the MQTT protocol to dispatch data coming from the field to backend services and alarms to the user.

* The **Resource Catalog** works as service and device registry system for all the actors in the system. It provides information about end-points (i.e. REST Web Services and MQTT topics) of all the devices, resources and services in the platform. It also provides configuration settings for applications and control strategies (e.g. alarm thresholds). 

* The **Smart Gateway** acts as an aggregator and bridge at the *Edge* level. It is responsible for the local management of poles and communication towards the Cloud.
    * On the "Field" side, it receives pre-processed data from individual poles (via Local MQTT).
    * On the "Cloud" side, it acts as a REST client to automatically register devices in the **Resource Catalog** upon power-up. It also works as an MQTT publisher to forward formatted data to the global Message Broker.

* The **Smart Pole (Device)** is the sensor node equipped with tilting, temperature, humidity, and GPS sensors. It performs local pre-processing (Edge Computing) to reduce data size and sends optimized JSON packets to the Smart Gateway via local protocols.

* The **Cloud Adaptor** is an MQTT subscriber that receives environmental and status measurements from the Broker and uploads them on the external storage platform (**ThingSpeak**) through REST Web Services. It ensures decoupling between the real-time data flow and persistent storage.

* **ThingSpeak** is a third-party software that provides REST Web Services. It is an open data platform for the Internet of Things used to store, post-process and visualize historical data (through plots).

* The **Data Analytics** is a backend logical component that monitors the health status of the poles. It works i) as an MQTT subscriber to receive telemetry data; ii) as a REST client to retrieve specific safety thresholds (configuration) from the **Resource Catalog**; iii) as an MQTT publisher to send "ALARM" messages into the system when values exceed critical thresholds.

* The **Dashboard** is the final user interface for technical monitoring. It retrieves and visualizes real-time data or alarms exploiting the MQTT protocol (subscribing to alarm topics). It also exploits REST Web Services provided by the **Resource Catalog** to retrieve geolocated metadata (GPS maps) and allows the operator to intervene (Human-in-the-loop actuation).
