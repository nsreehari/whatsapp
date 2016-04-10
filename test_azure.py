#!/opt/bitnami/python/bin/python
#-*- coding: utf-8 -*-


import sys
import json
from azure.servicebus import ServiceBusService, Message, Queue

bus_service = ServiceBusService(
    service_namespace='msgtestsb',
    shared_access_key_name='RootManageSharedAccessKey',
    shared_access_key_value='Ar9fUCZQdTL7cVWgerdNOB7sbQp0cWEeQyTRYUjKwpk=')


def send(mymsg):
    jsondict = {
      "msgtype": "text", "msgbody": mymsg, "medium": "BHH", "phonenum": "919701277758"
    }
    global bus_service
    msg = Message(json.dumps(jsondict))
    bus_service.send_queue_message('INPUT', msg)

def receive():
    global bus_service

    msg = bus_service.receive_queue_message('BHH_OUTPUT', peek_lock=False)
    try: 
        print "> ", json.loads(msg.body)['response']
    except:
        pass
    
def main(mymsg):
    try:
       if mymsg == "receive":
          while True:
             receive()
       elif mymsg == "send":
          while True:
             inp = raw_input("=> ") 
             send(inp)
       else:
           print mymsg
           send(mymsg)
           receive()
    except:
       pass

try:
       mymsg = sys.argv[1]
       main(mymsg)
except:
       mymsg = 'quote'
       print mymsg
       send(mymsg)
       receive()

