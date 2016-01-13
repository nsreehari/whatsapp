#!/opt/bitnami/python/bin/python
#-*- coding: utf-8 -*-


from copy import deepcopy
import json
from serve import *
from azure.servicebus import ServiceBusService, Message, Queue
import logging

logging.basicConfig(filename='/tmp/serving.log', level=logging.INFO)

class AzureConnection():
    def __init__(self):
        self.bus_service = ServiceBusService(
            service_namespace='msgtestsb',
            shared_access_key_name='RootManageSharedAccessKey',
            shared_access_key_value='Ar9fUCZQdTL7cVWgerdNOB7sbQp0cWEeQyTRYUjKwpk=')
        queue_options = Queue()
        queue_options.max_size_in_megabytes = '5120'
        queue_options.default_message_time_to_live = 'PT96H'

        self.bus_service.create_queue('process_incoming', queue_options)
        self.bus_service.create_queue('whatsapp_sender', queue_options)
        self.bus_service.create_queue('myapp_sender', queue_options)
 

    def receive(self):
        msg = self.bus_service.receive_queue_message('process_incoming', peek_lock=False)
        
        if msg != None and msg.body:
                logging.info( '%s ' % datetime.now() +  msg.body)
                return json.loads(msg.body)
        else:
                return None

    def send(self, jsondict):
        t = json.dumps(jsondict)
        msg = Message(t)
        logging.info( '%s ' % datetime.now() + t)
        Q = jsondict['medium'] + '_sender'
            
        self.bus_service.send_queue_message(Q, msg)


azureConn = AzureConnection()
serve = Serve()

from os.path import isfile
while not isfile('/home/bitnami1/whatsapp/.stopazure'):
    receivejson = azureConn.receive()
    if receivejson != None:
        resp = serve.getResponse(receivejson)
        if resp:
            if resp['restype'] == 'list':
                respc = deepcopy(resp)
                for (typ, val) in resp['response']:
                   respc['restype'] = typ
                   respc['response'] = val
                   azureConn.send(respc)
            else:
                azureConn.send(resp)
    else:
        time.sleep(2.6)
