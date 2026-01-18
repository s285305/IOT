import cherrypy
import json
import time
import os

class SmartCityCatalog:
    def __init__(self, filename='catalog.json'):
        self.filename = filename
        self.data = {}

        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                self.data = json.load(f)
            print(f"Catalogo caricato da {self.filename}")
        else:
            self.data = {
                "owner": "Group 6",
                "topic": {
                    "computeDecay":["poleData"],
                    "checkThreshold": {
                        'publish':['alert'],
                        'subscribe': ['poleData']
                    },
                    "dashboard":["alert"],
                    "cmd_topic": "poleCmd",
                    "gateway":["poleData"],
                    "interfaccia":["poleData"]
                },
                "central_broker": {"address": "127.0.0.1", "port": 1884},
                "local_broker": {"address": "127.0.0.1", "port": 1885},
                "c_d_url": "http://localhost:8090",
                "writer_port": 8090,
                "dashboard_port": 8081,
                "BackEnd": {
                    "computeDecay":'',
                    "checkThreshold":''
                },
                "db_info": { "influx_host": "http://localhost:8181","token": "apiv3_qkhm2kiMdFeqH7127QV_5-6dak5IwIrzr7Fy85eEnYpyXs2o46NdAvqqYm8BLUOWKxAO83-3UuoB9A9ikLpXVQ",
                            "db": "pole_measurements", "table":"pole_measurements"},
                "dashboard":"",
                "threshold": 20,
                "regions": {  "Piemonte": {
                "minLat": 44.1,
                "maxLat": 46.5,
                "minLon": 6.6,
                "maxLon": 9.2
            },
            "Valle d'Aosta": {
                "minLat": 45.6,
                "maxLat": 46.5,
                "minLon": 6.8,
                "maxLon": 7.9
            },
            "Lombardia": {
                "minLat": 44.8,
                "maxLat": 46.6,
                "minLon": 8.5,
                "maxLon": 11.5
            },
            "Trentino-Alto Adige": {
                "minLat": 45.7,
                "maxLat": 47.1,
                "minLon": 10.4,
                "maxLon": 12.5
            },
            "Veneto": {
                "minLat": 44.8,
                "maxLat": 46.6,
                "minLon": 10.7,
                "maxLon": 13.1
            },
            "Friuli-Venezia Giulia": {
                "minLat": 45.5,
                "maxLat": 46.7,
                "minLon": 12.3,
                "maxLon": 13.9
            },
            "Liguria": {
                "minLat": 43.8,
                "maxLat": 44.7,
                "minLon": 7.5,
                "maxLon": 10.1
            },
            "Emilia-Romagna": {
                "minLat": 43.7,
                "maxLat": 45.1,
                "minLon": 9.2,
                "maxLon": 12.8
            },
            "Toscana": {
                "minLat": 42.2,
                "maxLat": 44.5,
                "minLon": 9.6,
                "maxLon": 11.8
            },
            "Umbria": {
                "minLat": 42.6,
                "maxLat": 43.6,
                "minLon": 11.9,
                "maxLon": 12.9
            },
            "Marche": {
                "minLat": 42.7,
                "maxLat": 44.0,
                "minLon": 12.2,
                "maxLon": 13.9
            },
            "Lazio": {
                "minLat": 41.2,
                "maxLat": 42.9,
                "minLon": 11.4,
                "maxLon": 14.0
            },
            "Abruzzo": {
                "minLat": 41.6,
                "maxLat": 42.9,
                "minLon": 13.0,
                "maxLon": 14.8
            },
            "Molise": {
                "minLat": 41.4,
                "maxLat": 42.0,
                "minLon": 14.3,
                "maxLon": 15.1
            },
            "Campania": {
                "minLat": 40.0,
                "maxLat": 41.5,
                "minLon": 13.7,
                "maxLon": 15.8
            },
            "Puglia": {
                "minLat": 39.8,
                "maxLat": 42.1,
                "minLon": 14.8,
                "maxLon": 18.5
            },
            "Basilicata": {
                "minLat": 39.9,
                "maxLat": 41.3,
                "minLon": 15.3,
                "maxLon": 16.9
            },
            "Calabria": {
                "minLat": 37.9,
                "maxLat": 40.2,
                "minLon": 15.6,
                "maxLon": 17.2
            },
            "Sicilia": {
                "minLat": 36.6,
                "maxLat": 38.3,
                "minLon": 12.3,
                "maxLon": 15.7
            },
            "Sardegna": {
                "minLat": 38.9,
                "maxLat": 41.3,
                "minLon": 8.1,
                "maxLon": 9.9
            }
                },
                "gateways": []
            }
            self.save()
            print(f"Creato nuovo file {self.filename}")

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

    def _find_gateway(self, gateway_id):
        for i, gw in enumerate(self.data.get("gateways", [])):
            if gw.get("gateway_id") == gateway_id:
                return i, gw
        return None, None
    
    def _find_pole(self, gateway, pole_id):
        for i, pole in enumerate(gateway.get("smart_poles", [])):
            if pole.get("id") == pole_id:
                return i, pole
        return None, None

class computeDecay:
    exposed = True

    def __init__(self, catalog:SmartCityCatalog):
        self.catalog = catalog

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri, **params):
        body = cherrypy.request.json
        
            # 1. Assicuriamoci che la struttura esista nel dizionario data
        if 'BackEnd' not in self.catalog.data:
                self.catalog.data['BackEnd'] = {}
            
            # 2. Salviamo l'ID
        self.catalog.data['BackEnd']['computeDecay'] = body['id']
            
            # 3. Salviamo su file
        self.catalog.save()
        print(f"[*] Catalog aggiornato: computeDecay registrato con ID {body['id']}")
        return {"status": "success", "message": "computeDecay registered"}
    
class checkThreshold:
    exposed = True

    def __init__(self, catalog:SmartCityCatalog):
        self.catalog = catalog

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri, **params):
        body = cherrypy.request.json
            # 1. Assicuriamoci che la struttura esista nel dizionario data
        if 'BackEnd' not in self.catalog.data:
                self.catalog.data['BackEnd'] = {}
            
            # 2. Salviamo l'ID
        self.catalog.data['BackEnd']['checkThreshold'] = body['id']
            
            # 3. Salviamo su file
        self.catalog.save()
        print(f"[*] Catalog aggiornato: checkThreshold registrato con ID {body['id']}")
        return {"status": "success", "message": "checkThreshold registered"}
        
        

class GatewayAPI:
    exposed = True

    def __init__(self, catalog: SmartCityCatalog):
        self.catalog = catalog

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri, **params):
        input_data = cherrypy.request.json

        if 'gateway_id' not in input_data:
            raise cherrypy.HTTPError(400, "Manca gateway_id")

        zone = input_data.get("zone")
        gateway_id = input_data.get("gateway_id")
        # 1 gateway per zona (se già esiste un altro gateway in quella zona -> blocca)
        for gw in self.catalog.data.get("gateways", []):
            if gw.get("zone") == zone and gw.get("gateway_id") != gateway_id:
                raise cherrypy.HTTPError(409, f"Gateway già presente in zona {zone}")


        gateway_id = input_data["gateway_id"]
        i, gw = self.catalog._find_gateway(gateway_id)

        if gw is None:
            new_gw = dict(input_data)
            new_gw.setdefault("smart_poles", [])
            new_gw["last_update"] = time.time()
            self.catalog.data["gateways"].append(new_gw)
        else:
            # aggiorna SOLO i campi gateway, non la lista pali
            #se togli questo tranne time non ti aggiorna i campi gateway ogni volta che fa la richiesta post
            incoming = dict(input_data)
            incoming.pop("smart_poles", None)  
            self.catalog.data["gateways"][i].update(incoming)
            self.catalog.data["gateways"][i]["last_update"] = time.time()

        self.catalog.save()
        return {"status": "gateway_registered", "gateway_id": gateway_id}


class PoleAPI:
    exposed = True

    def __init__(self, catalog: SmartCityCatalog):
        self.catalog = catalog

    def _same_location(self, p, lat, lon, eps=1e-5):
        try:
            return abs(float(p.get("lat")) - float(lat)) <= eps and abs(float(p.get("long")) - float(lon)) <= eps
        except Exception:
            return False

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri, **params):
        input_data = cherrypy.request.json
        gateway_id = input_data.get("gateway_id")
        pole = dict(input_data)  # copia

        if not gateway_id:
            raise cherrypy.HTTPError(400, "Manca gateway_id")  

        if "id" not in pole:
            raise cherrypy.HTTPError(400, "Manca pole.id")     # fix messaggio

        if "lat" not in pole or "long" not in pole:
            raise cherrypy.HTTPError(400, "Manca lat/long nel payload")

        pole_id = pole["id"]
        

        i, gw = self.catalog._find_gateway(gateway_id)
        if gw is None:
            raise cherrypy.HTTPError(404, "Gateway non trovato")  

        current_poles = self.catalog.data["gateways"][i].get("smart_poles", [])
        if any(p.get("id") == pole_id for p in current_poles):
            raise cherrypy.HTTPError(400, "Il palo con questo id esiste già.")
        current_poles.append(pole)
        self.catalog.data["gateways"][i]["smart_poles"] = current_poles
        self.catalog.save()
        return {
            "status": "pole_created",
            "gateway_id": gateway_id,
            "id": pole_id,
        }
    
    def DELETE(self, *uri, **params):
        if len(uri) < 2:
            raise cherrypy.HTTPError(400, "Manca gateway_id o pole_id")

        gateway_id = uri[0]
        pole_id = uri[1]

        i, gw = self.catalog._find_gateway(gateway_id)
        if gw is None:
            raise cherrypy.HTTPError(404, "Gateway non trovato")  

        j, pole = self.catalog._find_pole(gw, pole_id)
        if pole is None:
            raise cherrypy.HTTPError(404, "Palo non trovato")  

        del self.catalog.data["gateways"][i]["smart_poles"][j]
        self.catalog.save()

        return {
            "status": "pole_deleted",
            "gateway_id": gateway_id,
            "id": pole_id,
        }

class DashboardAPI:
    exposed = True

    def __init__(self, catalog:SmartCityCatalog):
        self.catalog = catalog

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri, **params):
        body = cherrypy.request.json
        
        if body['id']:
            # 1. Assicuriamoci che la struttura esista nel dizionario data
            if 'dashboard' not in self.catalog.data:
                self.catalog.data['dashboard'] = ''
            
            # 2. Salviamo l'ID
            self.catalog.data['dashboard'] = body['id']
            
            # 3. Salviamo su file
            self.catalog.save()
            print(f"[*] Catalog aggiornato: ComputeDecay registrato con ID {body['id']}")
            return {"status": "success", "message": "ComputeDecay registered"}
        
        return {"status": "error", "message": "Unknown type"}
    
class interfaccia_dbAPI:
        exposed = True
        def __init__(self, catalog:SmartCityCatalog):
            self.catalog = catalog

        @cherrypy.tools.json_in()
        @cherrypy.tools.json_out()
        def POST(self, *uri, **params):
            body = cherrypy.request.json
            
            if body['id']:
                # 1. Assicuriamoci che la struttura esista nel dizionario data
                if 'interfaccia' not in self.catalog.data:
                    self.catalog.data['interfaccia'] = ''
                
                # 2. Salviamo l'ID
                self.catalog.data['interfaccia'] = body['id']
                
                # 3. Salviamo su file
                self.catalog.save()
                print(f"[*] Catalog aggiornato: interfaccia registrato con ID {body['id']}")
                return {"status": "success", "message": "interfaccia registered"}
            
            return {"status": "error", "message": "Unknown type"}


class RootAPI:
    exposed = True

    def __init__(self, catalog: SmartCityCatalog):
        self.catalog = catalog
        self.gateway = GatewayAPI(catalog)  # /gateway
        self.pole = PoleAPI(catalog)        # /pole
        self.computeDecay = computeDecay(catalog)  # 
        self.checkThreshold = checkThreshold(catalog)
        self.dashboard = DashboardAPI(catalog)
        self.interfaccia = interfaccia_dbAPI(catalog)

    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def GET(self, *uri, **params):
        if len(uri) == 0:
            return self.catalog.data
        
        if uri[0] == 'compute_id':
            if params:
                try:
                    id = ''
                    if params.get('type') == 'gateway':
                        id = 'gateway_'+str(params['lat'])+str(params['lon'])
                    else:
                        id = params.get('type')
                    return {"id": id}
                except Exception as e:
                    print('Error: ', e)

        if uri[0] == 'gateways':
            if len(uri) > 1:
                target_id = uri[1]
                _, gw = self.catalog._find_gateway(target_id)
                if gw is not None:
                    return gw
                raise cherrypy.HTTPError(404, "Gateway non trovato")
            return self.catalog.data['gateways']

        if uri[0] == 'smart_poles':
            if len(uri) > 2: 
                gateway_id = uri[1]
                pole_id = uri[2]
                _, gw = self.catalog._find_gateway(gateway_id)
                if gw is not None:
                    _, pole = self.catalog._find_pole(gw, pole_id)
                    if pole is not None:
                        return pole
                    raise cherrypy.HTTPError(404, "Palo non trovato")
                raise cherrypy.HTTPError(404, "Gateway non trovato")
            elif len(uri) == 2:
                gateway_id = uri[1]
                _, gw = self.catalog._find_gateway(gateway_id)
                if gw is not None:
                    return gw.get("smart_poles", [])
                raise cherrypy.HTTPError(404, "Gateway non trovato")

        if uri[0] == 'local_broker':
                return self.catalog.data['local_broker']
        if uri[0] == 'central_broker':
                return self.catalog.data['central_broker']

        if uri[0] == 'regions':
            if params.get('region'):
                region_name = params.get('region')
                regions = self.catalog.data['regions']
                if region_name in regions:
                    return regions[region_name]
                else:
                    raise cherrypy.HTTPError(404, "Regione non trovata")
            return self.catalog.data['regions']
        
        if uri[0] == "pole_status":
            if len(uri) < 2:
                raise cherrypy.HTTPError(400, "Missing pole_id")
            pole_id = uri[1]

            for gw in self.catalog.data.get("gateways", []):
                for p in gw.get("smart_poles", []):
                    if p.get("id") == pole_id:
                        return {"active": True}

            return {"active": False}  

        if uri[0] == 'threshold':
            return {"threshold": self.catalog.data.get('threshold', None)}
        
        if uri[0] == 'topic':
            if params:
                try:
                    return self.catalog.data['topic'][params['type']]
                except Exception as ex:
                    print('Error: ', ex)
            return self.catalog.data['topic']
        
        if uri[0]=='owner':
            return {"owner": self.catalog.data.get('owner', '')}
        
        if uri[0]=='checkThreshold':
            return self.catalog.data.get('checkThreshold', {})
        
        if uri[0]=='computeDecay':
            return self.catalog.data.get('computeDecay', {})
        
        if uri[0]=='dashboard':
            return self.catalog.data.get('dashboard', '')
        if uri[0]=='db_info':
            return self.catalog.data.get('db_info', {})
        if uri[0]=='writer_port':
            return {"writer_port": self.catalog.data.get('writer_port', 8090)}
        if uri[0]=='c_d_url':
            return {"c_d_url": self.catalog.data.get('c_d_url','')}
        if uri[0]=='dashboard_port':
            return {"dashboard_port": self.catalog.data.get('dashboard_port',8081)}
                

        raise cherrypy.HTTPError(400, "Comando non riconosciuto")

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self, *uri, **params):
        body = cherrypy.request.json

        if uri[0] == 'topic':
            if params:
                type = params.get('type')
                try:
                    topics = body.get('new_topics',[])
                    self.catalog.data['topic'][type]=topics
                    self.catalog.save()

                    print(f"[*] Catalog aggiornato: {self.catalog.data['topic'][type]}")
                    return {"status": "success", "message": f"Topics adjourned for {type}"}
                except Exception as e:
                    print('Impossible register new topic, error:', e)


if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }

    catalog = SmartCityCatalog('catalog.json')
    cherrypy.tree.mount(RootAPI(catalog), '/', conf)

    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.engine.start()
    cherrypy.engine.block()
