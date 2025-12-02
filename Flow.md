### Complete description of the system

The proposed IoT platform for Smart Poles Monitoring follows the microservices design pattern. It also exploits two communication paradigms: i) publish/subscribe based on the MQTT protocol and ii) request/response based on REST Web Services. This architecture includes custom backend processing for decay computation, threshold checking and a user interface based on a dashboard.

In this context, eight main actors have been identified and introduced in the following:

* *The Message Broker* provides asynchronous communication based on the publish/subscribe approach. It exploits the MQTT protocol to act as the central communication bus between the data acquisition layer, the analytics layer, and the user interface. In particular, at the data acquisition layer, two brokers can be found, corresponding to two different MQTT connections: the first, connects each Rasberry board to its closest gateway, while the second connects all of the gateways to the rest of the system.
* *The Resource Catalog* works as a service and device registry system for all the actors in the system. It provides information about end-points and configuration settings.
    * The *Smart Gateway* registers itself and the connected poles here via *REST POST*. 
    * *Data Analytics* retrieves configuration settings (e.g., threshold values) from here via *REST GET*.
    * *The Dashboard* retrieves system information from here to correctly visualize resources.
* *The Smart Poles* are edge devices located in the target area. They gather local sensor data and transmit it via a local MQTT instance ("MQTT Local"). These act as the primary data sources.
* *The Smart Gateway* acts as a bridge between the local field devices and the central infrastructure. It aggregates data from the Smart Poles and forwards it to the central system.
    * It works as an *MQTT Publisher* to send collected telemetry data to the *Message Broker*.
    * It uses *REST POST* to register devices with the *Resource Catalog*.
* *Data Analytics* is a backend service responsible for processing incoming telemetry.
    * It works as an *MQTT Subscriber* to receive "Data" topics from the Message Broker.
    * It implements a *"Check TH" (Threshold)* logic, comparing incoming data against configurations fetched from the Resource Catalog.
    * If a threshold is breached, it acts as a publisher, sending an *"ALARM"* message back to the Message Broker.
    * *"Compute Decay"* is a specialized backend processing unit, which processes data streams to calculate decay metrics.
    * It works as a *REST Client* to *POST* the computed results into the external *Database (DB)*.
* *The Database (DB)* is an external cloud-based storage service.
    * It receives processed data (via POST) from the *Compute Decay* service.
    * It provides historical data to the *Dashboard* via *REST GET* requests.
    * It receives telemetry data via MQTT from the central Message Broker as a *MQTT Subscriber*.
* *The Dashboard* is the user interface for the system.
    * It works as an *MQTT Subscriber* to receive real-time *"ALARM"* notifications from the Message Broker.
    * It communicates with the *Resource Catalog* to get system metadata.
    * It retrieves processed analytics and decay data from the external *Database* via *REST GET* to visualize the status of the monitored area.
