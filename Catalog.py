import cherrypy
import json
import time
import os

class SmartCityCatalog:
    exposed = True

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
                "central_broker": {
                    "address": "broker.hivemq.com",
                    "port": 1883
                },
                "gateways": [] 
            }

            self.save()
            print(f"Creato nuovo file {self.filename}")


    def save(self):
        with open(self.filename, 'w') as f:

            json.dump(self.data, f, indent=4) 

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri, **params):
        input_data = cherrypy.request.json
        
        if 'gateway_id' not in input_data:
            raise cherrypy.HTTPError(400, "Manca gateway_id")

        found_gateway = False
        

        for i, gw in enumerate(self.data['gateways']):
            if gw['gateway_id'] == input_data['gateway_id']:
                found_gateway = True
                

                current_poles = self.data['gateways'][i].get('smart_poles', [])
                

                self.data['gateways'][i].update(input_data)
                

                new_poles_list = input_data.get('smart_poles', [])
                
                for new_pole in new_poles_list:
                    pole_exists = False

                    for k, existing_pole in enumerate(current_poles):
                        if existing_pole['pole_id'] == new_pole['pole_id']:

                            current_poles[k] = new_pole
                            pole_exists = True
                            break
                    
                    if not pole_exists:

                        current_poles.append(new_pole)
                

                self.data['gateways'][i]['smart_poles'] = current_poles
                

                self.data['gateways'][i]['last_update'] = time.time()
                break
        

        if not found_gateway:
            input_data['last_update'] = time.time()

            if 'smart_poles' not in input_data:
                input_data['smart_poles'] = []
            self.data['gateways'].append(input_data)


        self.save()

        return {"status": "registered", "gateway_id": input_data['gateway_id']}

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        if len(uri) == 0:
            return self.data
        
        if uri[0] == 'gateway' and len(uri) > 1:
            target_id = uri[1]
            for gw in self.data['gateways']:
                if gw['gateway_id'] == target_id:
                    return gw
            raise cherrypy.HTTPError(404, "Gateway non trovato")
        
        if uri[0] == 'broker':
            return self.data['central_broker']

        raise cherrypy.HTTPError(400, "Comando non riconosciuto")

if __name__ == '__main__':
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    

    cherrypy.tree.mount(SmartCityCatalog('catalog.json'), '/', conf)
    
    cherrypy.config.update({'server.socket_host': '0.0.0.0'})
    cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.engine.start()
    cherrypy.engine.block()