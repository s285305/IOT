# IoT and Cloud for Sustainable Communities
## Complete Lecture Compilation (Lectures 1-15)

### Instructor: Lorenzo Bottaccioli
**Politecnico di Torino**

---

## TABLE OF CONTENTS

1. Introduction and IoT Fundamentals
2. Python Basics
3. Object-Oriented Programming (OOP)
4. Communication Paradigms and Protocols
5. Data Exchange in Web Environments (XML, HTML)
6. Web Programming and Services
7. Web Services with CherryPy
8. MQTT Protocol and Implementation
9. Communication Protocols Comparison
10. Software Requirements for IoT Platforms
11. Software Architecture Design Patterns
12. IoT Middleware Platforms (LinkSmart)
13. Services Lifecycle
14. Cloud Computing and IoT Systems
15. IoT for Smart Cities Applications

---

# LECTURE 1: INTRODUCTION TO IOT

## What is the Internet of Things?

The Internet of Things is a **giant network of connected devices** composed by several actors that could be software or hardware entities:
- Must be internet connected
- Equipped with a sensor or actuator
- Capable of collecting, storing, and analyzing data

**Main Goal:** Extract value from collected data - if no value is extracted, it's not an IoT application.

### Kevin Ashton's Definition (1999)

*"The Internet of Things connects everyday consumer objects and industrial equipment onto the network, enabling information gathering and management of these devices via software in order to increase efficiency, enable new services, or achieve other health, safety, or environmental benefits."*

### More Practical Definition

IoT refers to the **interconnection of uniquely identifiable embedded computing-like devices** within the existing Internet infrastructure.

## Enabling Technologies and Issues

### Key Technologies:
- **Sensors/Actuators** - Data collection and control mechanisms
- **Low power, autonomic, pervasive, ubiquitous computing** - Resource-constrained devices
- **Communication protocols** (REST, MQTT) - Device-to-device communication
- **Microservices and Middleware** - Software architecture
- **Data Analytics Engines** - Cloud-based analysis
- **Applications** (iOS, Android, Web) - User interfaces

---

# LECTURE 2: PYTHON BASICS

## Python Setup
- Download Python 3
- Download an editor (e.g., Sublime Text 2)
- Use command line for execution

## Data Types and Structures

### Lists
- Flexible arrays that can contain mixed types
- Example: `a = [99, "bottles of beer", ["on", "the", "wall"]]`
- Operations: `a+b`, `a*3`, `a[0]`, `a[-1]`, `a[1:]`, `len(a)`
- Item and slice assignment supported
- Common list operations: `append()`, `pop()`, `insert()`, `reverse()`, `sort()`

### Dictionaries
- Hash tables or "associative arrays"
- Example: `d = {"duck": "eend", "water": "water"}`
- Lookup: `d["duck"]` returns `"eend"`
- Operations: delete, insert, overwrite
- Keys must be immutable (numbers, strings, tuples)
- No restrictions on values

### Tuples
- Immutable versions of lists
- Example: `x = (1, 2, 3)`
- Special case for single element: `y = (2,)` (comma required)
- Empty tuple: `empty = ()`

## Reference Semantics

Important concept: **Assignment manipulates references, not copies**
- `x = y` makes `x` reference the same object as `y`
- Changes to mutable objects (like lists) affect all references
- Immutable objects (integers, strings) create new objects on assignment

---

# LECTURE 3: OBJECT-ORIENTED PROGRAMMING

## OOP Fundamentals

### Core Concepts

**Object:** A software item that contains:
- **Variables** - Data state
- **Methods** - Operations on data

**Class:** Describes objects with the same behavior

**Why OOP?**
- Programs are getting too large to be fully comprehensible
- Need for managing very-large projects
- Allows programmers to reuse large blocks of code
- Makes code reuse a real possibility
- Simplifies maintenance and evolution

### Main Principles of OOP

1. **Interface** - Set of messages an object can receive
2. **Encapsulation** - Restricting access to object components
3. **Inheritance** - Relationship between superclass and subclass
4. **Polymorphism** - Ability to treat objects of different classes uniformly

### Class Definition in Python

```python
class ClassName:
    "documentation"

    def __init__(self, arg1, arg2, ...):
        self.x = arg1
        self.y = arg2
        ...

    def method_name(self, arg1, arg2, ...):
        # method implementation
        ...
```

### Encapsulation Benefits

- **Simplified access** - Users need only understand the interface
- **Self-contained** - Implementation can proceed independently
- **Ease of evolution** - Implementation can change without affecting other code
- **Single point of change** - Data structure modifications in one location

### Inheritance Hierarchies

- **Superclass** - More generalized class
- **Subclass** - More specialized class inheriting from superclass
- Subclass inherits data (variables) and behavior (methods)

### Polymorphism

- Method calls are determined by the type of the actual object, not the variable type
- This is called **dynamic method lookup**
- Allows treating objects of different classes uniformly
- Makes programs easily extensible

---

# LECTURE 4: COMMUNICATION PARADIGMS AND PROTOCOLS

## Evolution of the Internet

- **1965** - Lawrence Roberts proposes computer networking
- **1969** - ARPANET established (BBN Group)
- **1974** - TCP/IP protocols developed (Vinto Cerf, Robert Kahn)
- **1986** - NSFNET established
- **1989** - Internet Service Providers (ISP)
- **1989** - Tim Berners-Lee invents World Wide Web
- **1993** - Mosaic browser released
- **1994** - Netscape and Yahoo launched
- **2000** - Dot-com bubble
- **2004** - Social media era begins (Facebook)
- **2007** - iPhone introduces mobile IoT
- **2010** - IoT concept emerges

## Network Protocol Stack

Each protocol layer appends:
- **Header (H)** - Control information
- **Footer** - Error checking and end markers

**Example:**
- Application Layer: `GET http://myurl:8080/my/resources`
- Transport Layer: Adds TCP header
- Internet Layer: Adds IP header (source/destination)
- Data Link Layer: Adds MAC addresses
- Physical Layer: Transmits over network

## Lightweight Protocols for IoT

Traditional protocols are NOT lightweight and unsuitable for resource-constrained IoT devices:
- Limited CPU
- Limited RAM
- Battery-powered

**Proposed lightweight protocols:**
- Bluetooth
- ZigBee
- Z-wave
- 6LoWPAN

## Interoperability Components

**Gateways or Device Connectors** are needed to:
- Allow interoperability between different devices
- Provide Internet connectivity
- Act as bridges between low-level hardware and TCP/IP networks

---

# LECTURE 5: DATA EXCHANGE IN WEB ENVIRONMENTS

## Requirements for Data Exchange

1. **Language to define abstract data types**
2. **System independent data representation** for any abstract data type
3. **Mechanisms for data receivers** to correctly decode data

## What is a Markup Language?

A system for annotating documents in a **syntactically distinguishable** way from text, describing:
- **Structural presentation** - Organization
- **Semantic aspects** - Meaning

## SGML (Standard Generalized Markup Language)

- **Meta-language** for describing markup languages
- Enables device/system independent documents
- Describes syntactic/structural aspects (not semantics)

**SGML Document:**
- Data object described by general markup language
- Text conformant to SGML syntactic rules
- Includes markups, textual data, and reference to DTD

**DTD (Document Type Definition):** Formalism describing specific markup language features

## HTML (HyperText Markup Language)

- Standard markup language for creating web pages
- Maintained by World Wide Web Consortium (W3C)
- Application of SGML
- Describes document structure semantically
- Web browsers render HTML into visible/audible pages

**HTML Example:**
```html
<!DOCTYPE html>
<html>
<head>
<title>This is a title</title>
</head>
<body>
<p>Hello world!</p>
</body>
</html>
```

## XML (eXtensible Markup Language)

**Key Features:**
- Language for formal description of markup languages
- Information sent in a "document"
- **Human and machine readable**
- Data incorporates information about their type
- Receivers don't need to know data types in advance

**Why XML?**
- Directly usable on the internet (via HTTP)
- Largely open and compatible
- Directly and simply usable by applications
- One of the main standards for data exchange

**XML Document Structure:**
- Tree structure
- Each sub-tree is an element
- Elements can include data or have attributes

**Well-formed XML Rules:**
1. Each non-empty element delimited by initial and final tag
2. Single root element containing all others
3. Attribute values always enclosed in quotes

---

# LECTURE 6: WEB PROGRAMMING

## Communication Paradigms

### Request/Response (Synchronous)

- Client **requests** data from server
- Server **responds** to the request
- Synchronous communication pattern
- Used in HTTP protocol

### Publish/Subscribe (Asynchronous)

- Removes dependencies between producer and consumer
- Allows loosely-coupled event-driven architectures
- Based on **Topics** (labels identifying communication flows)
- Allows (Near-)Real-time data transmission

**Architecture:**
- **Publishers** - Produce messages
- **Message Broker** - Routes messages based on topics
- **Subscribers** - Consume messages for specific topics

## Webserver

- Exposes **services** to clients
- Reachable via `host:port`
- **Port** - 16-bit unsigned number identifying process/service
- Must **always be up and running** ready to provide information
- Examples: `http://www.mywebsite.com:8080`, `http://192.168.1.34:8080`

## Webclient

- **Consumes** services exposed by webserver
- **Starts communication** by indicating host:port
- Makes requests and processes responses

## Web Service

**W3C Definition:** "A software system designed to support interoperable machine-to-machine interaction over a network."

**Key Characteristics:**
- Service offered by electronic device to another device
- Communication via World Wide Web
- Uses HTTP for machine-to-machine communication
- Transfers machine-readable formats: JSON and XML

---

# LECTURE 7: WEB SERVICES WITH CHERRYPY

## Why CherryPy?

CherryPy is a **pythonic, object-oriented web framework** that:
- Allows developers to **build web applications** much like any other object-oriented Python program
- Results in **smaller source code** developed in **less time**
- Provides minimal overhead for rapid development

## First Web Application

```python
import cherrypy

class HelloWorld(object):
    @cherrypy.expose
    def index(self):
        return "Hello world!"

if __name__ == '__main__':
    cherrypy.tree.mount(HelloWorld())
    cherrypy.engine.start()
    cherrypy.engine.block()
```

**Key Points:**
- `@cherrypy.expose` decorator exposes method as a URL
- Application accessible at `http://127.0.0.1:8080/`
- `cherrypy.tree.mount()` mounts application
- `engine.start()` and `engine.block()` start the server

## Session Support

```python
if __name__ == '__main__':
    conf = {
        '/': { 'tools.sessions.on': True }
    }
    cherrypy.tree.mount(StringGenerator(), '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
```

## Providing Static Resources

```python
conf = {
    '/': {
        'tools.sessions.on': True,
        'tools.staticdir.root': os.path.abspath(os.getcwd())
    },
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': './public'
    }
}
```

CherryPy maps `/static/css/style.css` to `public/css/style.css` on local disk.

---

# LECTURE 8: MQTT PROTOCOL

## MQTT Overview

**MQTT** (Message Queue Telemetry Transport):
- Publish-subscribe messaging protocol on top of TCP/IP
- Suitable for **event-driven architectures**
- Used in **Message Oriented Middleware**
- Used by Facebook in Facebook Messenger
- Ideal for smartphone and IoT applications

## Topic-Based Publish/Subscribe

### Topics
- Hierarchical structure using "/" as separator
- **Examples:**
  - `/sensor/1234/temperature`
  - `/sensor/1234/humidity`
  - `/sensor/567/temperature`
  - `/sensor/567/humidity`

### Wildcards in Subscriptions

**Only subscribers can use wildcards**

1. **Single-level wildcard (+)**
   - Matches exactly one level of hierarchy
   - Examples:
     - `/sensor/1234/+` - All data from sensor 1234
     - `/sensor/+/humidity` - Humidity from all sensors
     - `a/b/c/d` matches:
       - `+/b/c/d`
       - `a/+/c/d`
       - `a/+/+/d`
       - `+/+/+/+`

2. **Multi-level wildcard (#)**
   - Matches multiple levels of hierarchy
   - Must be at the end of subscription
   - Examples:
     - `a/b/c/d` matches:
       - `#`
       - `a/#`
       - `a/b/#`
       - `a/b/c/#`
   - Combined wildcards: `+/b/c/#`

---

# LECTURE 9: COMPARISON OF COMMUNICATION PROTOCOLS

## Messaging Protocols for IoT Systems

Different **Machine-to-Machine (M2M)** protocols addressing various IoT requirements:

### Widely Accepted Protocols

1. **HTTP** - Traditional web protocol
2. **CoAP** - Constrained Application Protocol
3. **MQTT** - Message Queue Telemetry Transport
4. **AMQP** - Advanced Message Queuing Protocol

Each addresses different IoT scenarios:
- Data collection in constrained networks
- Near-real-time data transmission
- Low latency requirements
- Bandwidth optimization

---

# LECTURE 10: SOFTWARE REQUIREMENTS FOR IOT PLATFORMS

## Main Requirements for IoT Platforms

1. **Interoperability**
   - Among heterogeneous systems, technologies, and devices
   - Example: PLC, Wi-Fi, ZigBee, different manufacturers

2. **Scalability**
   - Handle large number of sensors and devices
   - Support large number of users
   - Manage large volume of data (Big Data domain)
   - Process large volume of information exchanged

3. **Reliability**
   - Avoid or prevent possible failures
   - Prevent inconsistencies and overloads
   - Avoid data missing or corruption

4. **Evolve over Time**
   - Support rapid modification and enhancement
   - Low cost implementation
   - Small architectural impacts

5. **Modularity**
   - Design as collection of interoperable components
   - Communicate through lightweight mechanisms

6. **Extendibility**
   - Capability to add new functionality
   - Support software updating
   - Enable bug correction
   - Allow security policies and permissions updating

7. **Decentralization**
   - Each service implements functionalities with appropriate technology
   - Software components perform autonomously

8. **Flexibility**
   - Support heterogeneous services
   - Handle different characteristics and requirements

9. **Synchronous Communication**
   - Access historical data or device functionalities
   - Request/response approach

10. **Asynchronous Communication**
    - Near-real-time data transmission
    - Publish/subscribe approach
    - Event-based communication
    - Support low latency and scalability

11. **Standardization**
    - Foster data exchange through common interfaces
    - Web services and APIs
    - Open data formats

12. **Security**
    - Guarantee authentication
    - Ensure data access control
    - Maintain confidentiality and privacy

---

# LECTURE 11: SOFTWARE ARCHITECTURE DESIGN PATTERNS

## Web Resource

**Resource:** Any information that can be named
- Documents, images, etc.
- Has a **name and address represented by a URI**
- Can be stored and represented as stream of bits
- Example: document, database row, algorithm result

**Representation:** Sequence of bytes + representation meta-data
- Client receives representation when requesting resource
- Client sends representation when updating resource

### Key Principles

- Resource must have **at least one URI**
- **URI is name and address** of resource
- **URIs uniquely identify** resources regardless of type and representation
- **If no URI, not a resource** - not really on the Web

---

# LECTURE 12: IOT MIDDLEWARE PLATFORMS

## What is Middleware?

**Middleware** is computer software providing services beyond operating system:
- Described as **"software glue"**
- Makes easier for developers to perform communication and I/O
- Allows focus on specific purpose of application
- Connects software components or enterprise applications
- Software layer between operating system and applications

## Peer-to-Peer (P2P) Communication

**P2P communication paradigm:**
- Self-organizing of equal, autonomous entities (peers)
- Aims for shared usage of distributed resources
- Avoids central services
- Each peer acts as supplier and consumer
- Communication directly between peers

## LinkSmart Middleware

### Overview

**LinkSmart** - Middleware for heterogeneous IoT devices in distributed architecture

**Capabilities:**
- **Register, discover, and exploit** services and devices
- Overcomes incompatibility between proprietary protocols
- **Delivers development tools** for ambient intelligent applications
- **Abstracts IoT devices** as web services for uniform access

### Architecture Components

#### LocalConnect
Provides local connectivity and device management

**Core Components:**
1. **Service Catalog**
   - Service registry system
   - Exposes JSON-based RESTful API
   - Entry point for discovering services
   - Registers everything meant to be discovered

2. **Resource Catalog**
   - Device registry system
   - Registers available IoT devices
   - Lists resources exposed by devices
   - Exposes JSON-based RESTful API

3. **Device Connector/Gateway**
   - Provides integration of heterogeneous devices
   - Manages devices and resources in Resource Catalog
   - Provides communication with devices
   - Acts as gateway between hardware and TCP/IP network

#### GlobalConnect
Enables communication beyond private network boundaries

**Tunnelling Service:**
- Transparent communication across private networks
- Connects remote LocalConnect environments
- Border Gateways provide Tunnelling Service
- Enables exposure of local network to internet

---

# LECTURE 13: SERVICES LIFECYCLE

## What is a Service?

**OASIS Definition:** "A mechanism to enable access to one or more capabilities, where the access is provided using a prescribed interface and is exercised consistent with constraints and policies as specified by the service description."

**General Definition:**
- Software functionality or set of functionalities
- Purpose that different clients can reuse
- Exchanges information with other services through communication interfaces
- Operates over the Internet

### Service Domains

Services for Smart Cities can be applied in many domains:
- **Health** - Remote monitoring, diagnostics
- **Energy** - Smart grids, efficiency
- **Transportation** - Mobility management
- **Environment** - Air quality, weather
- **Disaster recovery** - Emergency response
- **Agriculture** - Crop management
- **Education** - E-learning
- **Infrastructure utilities** - Water, gas, electricity
- And many more...

### Stakeholders

- Municipalities, City Council, city administration
- National and regional governments
- City services companies
- Utility providers
- ICT Companies (Telecom, Start-ups, Software)
- NGOs
- International organizations
- Industry associations
- Academia and research organizations
- Citizens and citizen organizations
- Urban Planners
- Standardization bodies

## Use Cases

**Use Case Definition:** "List of actions or event steps, typically defining the interactions between an actor and a system to achieve a goal"

**Actor:** Can be human or external system (hardware/software)

**Use Case Analysis:** Important requirement analysis technique widely used in modern software engineering

## Services Lifecycle

General Service Lifecycle is a **continuous loop** with main phases:

### 1. Service Definition

- Service described highlighting main features and functionalities
- Stakeholder needs identified
- Basic requirements gathered

### 2. Service Design

- **Requirements analyzed**
- Functions and features identified
- Interoperability with other entities determined
- Different service functions allocated to system entities
- Concrete use cases modeled under different scenarios

### 3. Service Implementation

- **Information exchange ensured** between system entities
- Service integration performed
- Verification and validation completed
- Proper testing methodologies applied

### 4. Service Delivery

- Service **continuously monitored**
- Ensure meeting pre-set **KPIs (Key Performance Indicators)**
- Potential service improvements identified
- Enhancements that become new services

### 5. Service Decommission

- Activities related to disposal or replacement of service
- Lifecycle can begin again with service re-definition

---

# LECTURE 14: CLOUD COMPUTING AND IOT SYSTEMS

## IoT Software Infrastructure

**Distributed Software Platform** - Key concept

### Current IoT Ecosystems

Nowadays, IoT ecosystems composed by:
- **Various software stacks running on host computers**
- Servers or **cloud systems**
- Used for data processing and storage
- Authentication and service/device registry

### Supported Capabilities

IoT platforms support:
- **Data stream processing** - Real-time data handling
- **Complex event processing** - Event correlation and analysis
- **Machine learning** - Predictive and analytical models
- **Big data analytics** - Large-scale data analysis

---

# LECTURE 15: IOT FOR SMART CITIES

## Smart Grid Introduction

### Energy Market Context

**European Directive:** "Common rules for the internal market in electricity"

**Current Situation:**
- Market working properly for big producers, retailers, users
- **Small consumers and prosumers** cannot access directly
- Cannot be influenced by price signals

### Challenges

**Renewable Energy Integration:**
- Distributed generation from renewable, non-programmable sources becoming widespread
- Requires more flexible management of distribution grids

## The FLEXMETER Case Study

### Background

**Need for:** Flexible smart metering architecture for multiple energy vectors

### FLEXMETER Objectives

1. **Integrate** already available components and devices
2. **Combine and correlate information** from meters of different utilities (electricity, water, gas, heating)
3. **Provide** advanced services to users, DSOs, other utilities
4. **Enhance the retail market**

### FLEXMETER Approach

*"A metering infrastructure is an enabling technology that needs to be coupled with innovative services to reach energy management by means of rewards, automation and information."*

**Distributed Architecture** for managing heterogeneous data sources and (near-)real-time data processing

### Key Technologies

1. **Multi-services approach**
   - Uses information from electric, water, gas, heating meters
   - Provides general purpose services

2. **Substation meters**
   - Improve fault tolerance
   - Demand response capabilities
   - Consider local generation and storage

3. **Non-Intrusive Load Monitoring (NILM)**
   - Advanced techniques to profile user behaviors
   - Discern consumption of appliances from aggregated data

4. **Energy forecast algorithms**
   - Predict future consumption patterns

5. **Demand response algorithms**
   - Exploit information about energy flows
   - Use NILM profiles

### FLEXMETER Software Architecture

**Microservices approach** organized in three layers:

#### 1. Device Integration Layer
- Enables interoperability across heterogeneous devices and simulators
- Integrates different components

#### 2. Middleware Layer
- **Publish/Subscribe communication** through MQTT
- **Non-relational databases** for Big Data management
- Manages bi-directional device communication
- Manages asset information (people, places, things)
- Handles device-application interactions
- Provides **REST web services** for information access and entity management

#### 3. Application Layer
- Provides tools and API for distributed applications development
- User interfaces and services

---

## SMART HEALTH APPLICATIONS

### IoT Platform for Smart Health

**Purpose:** Provide services for remote chronic metabolic diseases monitoring and analysis

**Target:** Dialysis and diabetic patients

**Architecture:** Similar microservices approach with four layers:
1. Device Integration Layer
2. Middleware Layer
3. Services Layer
4. Application Layer

### Example Applications

1. **MyUrinalysis**
   - Urinalysis monitoring for diabetic patients
   - Remote data collection and analysis

2. **My Dialysis Diary**
   - Dialysis treatment tracking
   - Patient health monitoring
   - Data logging and analysis

---

## CONCLUSION

### Key Takeaways

1. **IoT Ecosystem:** Complex integration of sensors, devices, middleware, and cloud systems

2. **Architecture:** Multi-layered approach with device integration, middleware, and application layers

3. **Communication:** Multiple protocols (HTTP, MQTT, CoAP) supporting synchronous and asynchronous patterns

4. **Services:** Carefully designed with proper lifecycle from definition through delivery and decommissioning

5. **Applications:** Smart Cities, Healthcare, Energy Management showing real-world implementations

6. **Technologies:** Python, Web Services, MQTT, RESTful APIs as key tools for IoT development

---
