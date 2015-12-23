from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback

import time
from copy import copy
import pickle
import random
import requests

class EchoLayer(YowInterfaceLayer):
    tagqueue = {}
    stagetag = {}

    def chitchatresponse(self, messageBody):

        chitchat_file = open('chitchat.pkl', 'rb')
        chitchat = pickle.load(chitchat_file)
        chitchat_file.close()

        if messageBody.lower() in chitchat.keys():
            return chitchat[messageBody.lower()].strip()
        else:
            return ""

    def APIresponse(self, messageBody):

        urlToHit = "http://relequ07/JarvisTest/api/values/FetchResponse?query=" + messageBody.lower()
        req = requests.get(urlToHit)
        response = req.text[2:-2]
        return response.replace('\\','')
        #return " ".join(req.text.split('"')[1:-1])


    def getquote(self):

        lovequote_file = open('lovequotes.pkl', 'rb')
        lovequotes = pickle.load(lovequote_file)
        lovequote_file.close()

        return random.choice(lovequotes)

    def gethelpstring(self):
        helpstring = "I did not understand that but I have a set of amazing things you can try\n"
        helpstring = helpstring + "#quote : For those soulful quotes :)\n"
        helpstring = helpstring + "#name <Friend's name> : Just tell your friend's name and check what happens!\n"
        helpstring = helpstring + "#new : Keep yourself updated with what's new with me\n"
        return helpstring


    def parsecapabilities(self, messageBody, phonenum):

        keyword = messageBody.split()[0]

        if keyword == "#quote":
            return ('text', self.getquote())
        elif keyword == "#name":
            return ('text', "Wait, I will soon have something cool")
        elif keyword == "#new":
            return ('text', "I am so fresh on the block ... that's new i guess :)")
        elif keyword == "#savetag":
            keywords = messageBody.split()
            if len(keywords) != 2:
                return ('text', 'Invalid SAVETAG')
            tagname = '#' + keywords[1].strip('#')
            if tagname in self.tagqueue.keys():
                return ('text', 'Invalid SAVETAG: Given tag already exists')

            self.stagetag[phonenum] = tagname
            return ('text', 'Please send the content for tag: ' + tagname)

        elif keyword in self.tagqueue.keys():
            return ('readymade', self.tagqueue[keyword])
        else:
            return ('text', self.gethelpstring())


    def genresponse(self, messageProtocolEntity):

        NOHANDLEMSG = 'I do not handle these messages'

        phonenum = messageProtocolEntity.getFrom(False)
        print phonenum
        print self.stagetag
        if phonenum in self.stagetag.keys():
            tagname = self.stagetag[phonenum]

            self.tagqueue[tagname] = copy(messageProtocolEntity)

            #backup the self.tagqueue pending

            del self.stagetag[phonenum]

            return messageProtocolEntity

        if messageProtocolEntity.getType() == 'media':
            #for now, for all media messages, response is just echoed
            #messageProtocolEntity.setBody(NOHANDLEMSG)
            return messageProtocolEntity

        if messageProtocolEntity.getType() == 'text':
            messagebody = messageProtocolEntity.getBody()
            if messagebody.startswith("#"):
                (restype, response) = self.parsecapabilities(messagebody, phonenum)
            else:
                #(restype, response) = self.chitchatresponse(messagebody)
                #(restype, response) = self.APIresponse(messagebody)
                messageProtocolEntity.setBody(NOHANDLEMSG)
                return messageProtocolEntity

            if (restype == 'text'):
                if response != "" and response != "<no results>" and len(response) < 250:
                    safe_response = response.encode('ascii','ignore')
                    messageProtocolEntity.setBody(safe_response)
                elif len(messagebody.split(' ')) == 1:
                    messageProtocolEntity.setBody(":)")
                else:
                    messageProtocolEntity.setBody("Can I answer every question? Nobody likes a know-it-all!!!")

                return messageProtocolEntity

            if (restype == 'readymade'):
                return response

    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):

        if messageProtocolEntity.getType() == 'text':
            #time.sleep(0.454)
            print messageProtocolEntity.getBody()

        response = self.genresponse(messageProtocolEntity)

        if response.getType() == 'text':
            self.onTextMessage(response)
        elif response.getType() == 'media':
            self.onMediaMessage(response)

        self.toLower(response.forward(messageProtocolEntity.getFrom()))
        self.toLower(messageProtocolEntity.ack())
        self.toLower(messageProtocolEntity.ack(True))

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        self.toLower(entity.ack())

    def onTextMessage(self,messageProtocolEntity):
        print("Echoing %s to %s" % (messageProtocolEntity.getBody(), messageProtocolEntity.getFrom(False)))


    def onMediaMessage(self, messageProtocolEntity):
        if messageProtocolEntity.getMediaType() == "image":
            print("Echoing image %s to %s" % (messageProtocolEntity.url, messageProtocolEntity.getFrom(False)))

        elif messageProtocolEntity.getMediaType() == "location":
            print("Echoing location (%s, %s) to %s" % (messageProtocolEntity.getLatitude(), messageProtocolEntity.getLongitude(), messageProtocolEntity.getFrom(False)))

        elif messageProtocolEntity.getMediaType() == "vcard":
            print("Echoing vcard (%s, %s) to %s" % (messageProtocolEntity.getName(), messageProtocolEntity.getCardData(), messageProtocolEntity.getFrom(False)))


