#!/opt/bitnami/python/bin/python
#-*- coding: utf-8 -*-


import sys
import json
from azure.servicebus import ServiceBusService, Message, Queue

bus_service = ServiceBusService(
    service_namespace='msgtestsb',
    shared_access_key_name='RootManageSharedAccessKey',
    shared_access_key_value='Ar9fUCZQdTL7cVWgerdNOB7sbQp0cWEeQyTRYUjKwpk=')

try:
   mymsg = sys.argv[1]
except:
   mymsg = 'quote'


jsondict = {
    "msgtype": "text", "msgbody": mymsg, "medium": "myapp", "phonenum": "919701277758"
}

msg = Message(json.dumps(jsondict))
bus_service.send_queue_message('process_incoming', msg)


msg = bus_service.receive_queue_message('myapp_sender', peek_lock=False)
print
print json.loads(msg.body)['response']
print

