
import logging
import time
from copy import copy
import cPickle
import random
import json
#import requests
from urllib import urlretrieve
from sys import version_info
from datetime import datetime
from os.path import isfile, basename
from subprocess import call

logger = logging.getLogger(__name__)

def stitchmessage(j, phonenum, tagname):
     logger.info("Attaching content for " + tagname)
     if j['msgtype'] == 'text':
         stt = ['text', j['msgbody']]
         return stt
     elif j['msgtype'] == 'media':
       if j['mediatype'] in ['image', 'audio', 'video']:
         url = j['mediaurl']
         savepath = '/tmp/serve/repo_' + basename(mediaurl)
         urlretrieve(url, savepath)
         if isfile(savepath):
             stt = [j['mediatype'], {'localfile':savepath, 'caption': j['caption']}]
             return stt
         else:
             stt = [j['mediatype'], {'mediaurl':j['mediaurl'], 'caption': j['caption']}]
             return stt
       elif j['mediatype'] in ['location']:
         stt = [j['mediatype'], {'lat':j['lat'], 'long':j['long'], 'encoding':j['encoding'], 'name':j['name'], 'url':j['url']}]
         return stt
       elif j['mediatype'] in ['vcard']:
         stt = [j['mediatype'], {'name':j['name'], 'carddata':j['carddata']}]
         return stt

class GetSet():
    def __init__(self, cbfn=None):
        self.TAGSFILE = '/tmp/serve/tags_getset.pkl'
        self.stagetag = {}
        self.topickle = { 'tags': {} }

        try:
            tagsfile = open(self.TAGSFILE, "rb")
            self.topickle = cPickle.load(tagsfile)
            tagsfile.close()
        except IOError:
            pass

        self.tagqueue = self.topickle['tags']

    def flushpickle(self):
        output = open(self.TAGSFILE, 'wb')
        cPickle.dump(self.topickle, output)
        output.close()

    def preparse(self, j, phonenum):
      
        if phonenum in self.stagetag.keys():
            tagname = self.stagetag[phonenum].lower()

            stt = stitchmessage(j, phonenum, tagname)
            if tagname.startswith("append__"):
                tagname = tagname[8:]
                if tagname in self.tagqueue.keys():
                    self.tagqueue[tagname].append(stt)
                else:
                    self.tagqueue[tagname] = [ stt ]
            else: 
                self.tagqueue[tagname] = [ stt ]

            #flush the self.tagqueue to disk
            self.flushpickle()

            del self.stagetag[phonenum]

            return ('text', 'Successfully attached to tag:' + tagname)
        else:
            return None

    def parse(self, messageBody, phonenum):
        keyword = messageBody.split()[0].lower()
        if keyword == "get":
            keywords = messageBody.split()
            tagname = keywords[1].lower()
            if tagname in self.tagqueue.keys():
                return ('list', self.tagqueue[tagname])

        elif keyword == "set":
            keywords = messageBody.split()
            if len(keywords) != 2:
                return ('text', 'Invalid TAGNAME')
            tagname = keywords[1]
            if tagname in self.tagqueue.keys():
                return ('text', 'Invalid TAGNAME: Given tag already exists -- Use APPEND TAGNAME to attach the content to and existing tag or RESET TAGNAME to reset existing tag')

            self.stagetag[phonenum] = tagname
            return ('text', 'Please send the content for tag: ' + tagname)

        elif keyword == "append":
            keywords = messageBody.split()
            if len(keywords) != 2:
                return ('text', 'Invalid TAGNAME')
            tagname = keywords[1]
            if tagname not in self.tagqueue.keys():
                return ('text', 'Invalid TAGNAME: Given tag doesn"t exist')

            self.stagetag[phonenum] = "append__" + tagname
            return ('text', 'Please send the content for tag: ' + tagname)

        elif keyword == "reset":
            keywords = messageBody.split()
            if len(keywords) != 2:
                return ('text', 'Invalid tag')
            tagname = keywords[1]
            if tagname not in self.tagqueue.keys():
                return ('text', 'Invalid TAG: Given tag does not exist')

            self.stagetag[phonenum] = tagname
            return ('text', 'Please send the content for tag: ' + tagname)

        return None




class Serve():

    def __init__(self, cbfn=None):

                
        call("mkdir -p /tmp/serve".split())
        self.callbackfn = cbfn

        self.subparsers = [ GetSet() ]


    def downloadURL(self, url, savepath):
        urlretrieve(url, savepath)
        return 


    def getquote(self):

        quote_file = open('quotes.pkl', 'rb')
        quotes = cPickle.load(quote_file)
        quote_file.close()

        return random.choice(quotes)

    def gethelpstring(self):
        helpstring = "I do not understand that. You can try something like 'quote' or 'img'"
        return helpstring


    def parser(self, messageBody, phonenum):

        for sp in self.subparsers:
            ret = sp.parse(messageBody, phonenum)
            if ret:
                return ret

        keyword = messageBody.split()[0].lower()

        if keyword.lower() == "quote":
            return ('text', self.getquote())
        elif keyword == "name":
            return ('text', "Wait, I will soon have something cool")
        elif keyword == "img":
            try:
                image_number = messageBody.split()[1]
                if image_number not in ['1', '2', '3', '4', '5', '6', '7']:
                    image_number = '1'
            except:
                image_number = '1'
            return ('image', '/home/bitnami1/bhandara/website/img/t%s.jpg' % image_number )
        else:
            return ('text', self.gethelpstring())


    def getResponse(self, jsondict):

        ret = lambda a,b: {'phonenum':jsondict['phonenum'], 'medium':jsondict['medium'] ,'restype': a, 'response': b}

        phonenum = jsondict['phonenum']
        #logger.info( self.stagetag)

        for sp in self.subparsers:
            ret1 = sp.preparse(jsondict, phonenum)
            if ret1:
                (a, b) = ret1
                return ret(a, b)

        if jsondict['msgtype'] == 'text':
            messagebody = jsondict['msgbody']
            (restype, response) = self.parser(messagebody, phonenum)
            return ret(restype, response)

        if jsondict['msgtype']  == 'mediaaa':

            if jsondict['mediatype']  in ("image"):
                media_url = jsondict['mediaurl'] 
                TEMPDOWNLOADFILE = '/tmp/X.jpg'
                savepath = TEMPDOWNLOADFILE
                self.downloadURL( media_url, savepath)
                call(["/home/bitnami1/bhandara/gitpush.script"])
                return ret('text', 'saved %s' % 8)
            return ret('text', 'no media messages are handled')

        return None

    def getResponseWrapper(self, jsondict, recdMsg):
        inputjson = json.loads(jsondict)
        resp = self.getResponse(inputjson)
        return json.dumps(resp)
        
        


