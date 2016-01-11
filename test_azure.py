

import json
from azure.servicebus import ServiceBusService, Message, Queue

import sys

bus_service = ServiceBusService(
    service_namespace='msgtestsb',
    shared_access_key_name='RootManageSharedAccessKey',
    shared_access_key_value='Ar9fUCZQdTL7cVWgerdNOB7sbQp0cWEeQyTRYUjKwpk=')



#jsondict = {
#  'medium': 'myapp',
#  'phonenum': '919701277758',
#  'restype': 'text',
#  'response': 'Daily Quote: ENERGY: Conservation of energy means you have more energy at your disposal for right use - because Nature does not distinguish between good energy and bad energy. There is only energy. Energy is either used or energy is wasted.'
#}
#msg = Message(b'')
#msg = Message(json.dumps(jsondict))
#bus_service.send_queue_message('whatsapp_sender', msg)

try:
   mymsg = sys.argv[1]
except:
   mymsg = 'Hi, bb How are you?'


jsondict = {
    "msgtype": "text", "msgbody": mymsg, "medium": "myapp", "phonenum": "919701277758"
}

msg = Message(json.dumps(jsondict))
bus_service.send_queue_message('process_incoming', msg)


msg = bus_service.receive_queue_message('myapp_sender', peek_lock=False)
print
print(json.loads(msg.body)['response'])
print

#msg = bus_service.receive_queue_message('taskqueue', peek_lock=False)
#print(msg.body)
