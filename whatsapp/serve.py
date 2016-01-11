
import logging
import time
from copy import copy
import cPickle
import random
import json
import requests
from urllib import urlretrieve
from sys import version_info
from datetime import datetime

logger = logging.getLogger(__name__)

TAGSFILE = '/tmp/tagsfile.pkl'
TEMPDOWNLOADFILE = '/tmp/X.jpg'


class Serve():

    def __init__(self, cbfn=None):
        self.tagqueue = {}
        self.stagetag = {}

        self.callbackfn = cbfn

        try:
        	tagsfile = open(TAGSFILE, "rb")
        	self.tagqueue = cPickle.load(tagsfile)
        	tagsfile.close()
        except IOError:
        	pass


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


    def parsecapabilities(self, messageBody, phonenum):

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

        elif keyword == "get":
            keywords = messageBody.split()
            tagname = keywords[1].lower()
            if tagname in self.tagqueue.keys():
                return (self.tagqueue[tagname][0], self.tagqueue[tagname][1])
        elif keyword == "set":
            keywords = messageBody.split()
            if len(keywords) != 2:
                return ('text', 'Invalid TAGNAME')
            tagname = keywords[1]
            if tagname in self.tagqueue.keys():
                return ('text', 'Invalid TAGNAME: Given tag already exists')

            self.stagetag[phonenum] = tagname
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
        else:
            return ('text', self.gethelpstring())


    def getResponse(self, jsondict):

        ret = lambda a,b: {'phonenum':jsondict['phonenum'], 'medium':jsondict['medium'] ,'restype': a, 'response': b}

        phonenum = jsondict['phonenum']
        #logging.info( self.stagetag)
        if phonenum in self.stagetag.keys():
            tagname = self.stagetag[phonenum].lower()

            try:
                self.tagqueue[tagname] = ['readymade', copy(jsondict['msg'])]
            except:
                self.tagqueue[tagname] = ['text', jsondict['msgbody']]

            #backup the self.tagqueue pending
            output = open(TAGSFILE, 'wb')
            cPickle.dump(self.tagqueue, output)
            output.close()

            del self.stagetag[phonenum]

            return ret('text', 'Successfully attached to tag:' + tagname)


        if jsondict['msgtype']  == 'media':

            if jsondict['mediatype']  in ("image"):
                media_url = jsondict['mediaurl'] 
                savepath = TEMPDOWNLOADFILE
                self.downloadURL( media_url, savepath)
		from subprocess import call
                call(["/home/bitnami1/bhandara/gitpush.script"])
            	return ret('text', 'saved %s' % 8)
            return ret('text', 'no media messages are handled')

        if jsondict['msgtype'] == 'text':
            messagebody = jsondict['msgbody']
            (restype, response) = self.parsecapabilities(messagebody, phonenum)
            return ret(restype, response)

    def getResponseWrapper(self, jsondict):
        return json.dumps(self.getResponse(json.loads(jsondict)))
        
        


