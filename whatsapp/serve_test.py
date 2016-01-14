#!/opt/bitnami/python/bin/python
#-*- coding: utf-8 -*-


from copy import deepcopy
import json
from serve import *


serve = Serve()

from os.path import isfile
while True:
    mymsg = raw_input("=> ") 
    jsondict = {
      "msgtype": "text", "msgbody": mymsg, "medium": "myapp", "phonenum": "919700000000"
    }
    receivejson = json.dumps(jsondict)
    if receivejson != None:
        resp = serve.getResponse(jsondict)
        if resp:
            if resp['restype'] == 'list':
                respc = deepcopy(resp)
                for (typ, val) in resp['response']:
                   respc['restype'] = typ
                   respc['response'] = val
                   print respc
            else:
                print resp
    else:
        time.sleep(0.1)
