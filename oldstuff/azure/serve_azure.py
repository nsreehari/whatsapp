#!/opt/bitnami/python/bin/python
#-*- coding: utf-8 -*-


from copy import deepcopy
import json
from bhh import *
from azure.servicebus import ServiceBusService, Message, Queue
import logging

INPUTQUEUE = "INPUT"
OUTPUTQUEUE = "BHH"

#logging.basicConfig(filename='/tmp/serving.log', level=logging.INFO)
# Enable logging
logging.basicConfig(filename="/tmp/serving.log",
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

logger = logging.getLogger(__name__)

queue_options = Queue()
queue_options.max_size_in_megabytes = '5120'
queue_options.default_message_time_to_live = 'PT96H'

class AzureConnection():
    def __init__(self):
        self.bus_service = ServiceBusService(
            service_namespace='msgtestsb',
            shared_access_key_name='RootManageSharedAccessKey',
            shared_access_key_value='Ar9fUCZQdTL7cVWgerdNOB7sbQp0cWEeQyTRYUjKwpk=')

        self.bus_service.create_queue(INPUTQUEUE, queue_options)
        self.bus_service.create_queue(OUTPUTQUEUE + '_OUTPUT', queue_options)
 

    def receive(self):
        msg = self.bus_service.receive_queue_message(INPUTQUEUE, peek_lock=False)
        
        if msg != None and msg.body:
                logger.info(  msg.body)
                return json.loads(msg.body)
        else:
                return None

    def send(self, jsondict):
        t = json.dumps(jsondict)
        msg = Message(t)
        logger.info(  t)
        Q = jsondict['medium'] + '_OUTPUT'
            
        self.bus_service.create_queue(Q, queue_options)
        #logger.info( msg )
        self.bus_service.send_queue_message(Q, msg)


azureConn = AzureConnection()
serve = Serve()

from os import unlink
from os.path import isfile

def runloop():
  while not isfile('/home/bitnami1/whatsapp/.stopazure'):
   try:
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

    unlink('/home/bitnami1/whatsapp/.stopazure')
   except:
    pass

runloop()
