
import logging
import time
from copy import copy
import cPickle
import random
import requests
from urllib import urlretrieve
from sys import version_info

logger = logging.getLogger(__name__)

TAGSFILE = '/tmp/tagsfile.pkl'
TEMPDOWNLOADFILE = '/tmp/X.jpg'

class Serve():

    def __init__(self):
        self.tagqueue = {}
        self.stagetag = {}

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

        elif keyword == "savetag":
            keywords = messageBody.split()
            if len(keywords) != 2:
                return ('text', 'Invalid SAVETAG')
            tagname = keywords[1]
            if tagname in self.tagqueue.keys():
                return ('text', 'Invalid SAVETAG: Given tag already exists')

            self.stagetag[phonenum] = tagname
            return ('text', 'Please send the content for tag: ' + tagname)

        elif keyword == "updatetag":
            keywords = messageBody.split()
            if len(keywords) != 2:
                return ('text', 'Invalid tag')
            tagname = keywords[1]
            if tagname not in self.tagqueue.keys():
                return ('text', 'Invalid UPDATE TAG: Given tag does not exist')

            self.stagetag[phonenum] = tagname
            return ('text', 'Please send the content for tag: ' + tagname)
        else:
            return ('text', self.gethelpstring())


    def getResponse(self, message):

        phonenum = message.getFrom(False)
        logging.info( phonenum)
        #logging.info( self.stagetag)
        if phonenum in self.stagetag.keys():
            tagname = self.stagetag[phonenum].lower()

            self.tagqueue[tagname] = copy(message)

            #backup the self.tagqueue pending
            output = open(TAGSFILE, 'wb')
            cPickle.dump(self.tagqueue, output)
            output.close()

            del self.stagetag[phonenum]

            return ('text', 'Successfully attached to tag:' + tagname)

        if message.getType() == 'text':
            messagebody = message.getBody()
            keyword = messagebody.split()[0].lower()
            if keyword in self.tagqueue.keys():
                   return ('readymade', self.tagqueue[keyword])

        if message.getType() == 'media':

            if message.getMediaType() in ("image"):
                media_url = message.getMediaUrl()
                savepath = TEMPDOWNLOADFILE
                self.downloadURL( media_url, savepath)
		from subprocess import call
                call(["/home/bitnami1/bhandara/gitpush.script"])
            	return ('text', 'saved %s' % 8)
            return ('text', 'no media messages are handled')

        if message.getType() == 'text':
            messagebody = message.getBody()
            (restype, response) = self.parsecapabilities(messagebody, phonenum)
            return (restype, response)


