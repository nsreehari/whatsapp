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
      "msgtype": "json", "msgbody": mymsg, 
      "medium": "BHH1", "phonenum": "919701277758"
    }
    global bus_service
    msg = Message(json.dumps(jsondict))
    bus_service.send_queue_message('INPUT', msg)

def receive():
    global bus_service

    msg = bus_service.receive_queue_message('BHH1_OUTPUT', peek_lock=False)
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
       mymsgschema = {
        "FormName": "Visitor Entry",
        "TemplateName": "visitor",
        "Keywords": ["visitor entry", "entry", "visitor"],
        "fields": [
                {
                        "DisplayName": "Visitor Name",
                        "type": "text",
                        "id": "name",
                        "optional": "false"
                }, 
                {
                        "DisplayName": "Visitor Contact Number",
                        "type": "text",
                        "id": "vcontact",
                        "optional": "false"
                },
                {
                        "DisplayName": "Visitor Address",
                        "type": "text",
                        "id": "vaddress",
                        "optional": "false"
                },
                {
                        "DisplayName": "Host Name",
                        "type": "text",
                        "id": "hname",
                        "optional": "false"
                },
                {
                        "DisplayName": "Host Contact Number",
                        "type": "text",
                        "id": "hcontact",
                        "optional": "false"
                },
                {
                        "DisplayName": "Host approved",
                        "type": "checkbox",
                        "id": "happroved",
                        "Options": ["yes"],
                        "optional": "false"
                }
        ]

               }
       mymsg = {'action':'createtable', 'tablename':'table1', 'schema':mymsgschema}
       print mymsg
       send(mymsg)
#       receive()

