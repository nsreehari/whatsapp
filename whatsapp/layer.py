from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_media.protocolentities import RequestUploadIqProtocolEntity, ImageDownloadableMediaMessageProtocolEntity, AudioDownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_media.mediauploader import MediaUploader 
from yowsup.layers.protocol_media.mediadownloader import MediaDownloader 

import logging
import time
from copy import copy
import cPickle
import random
import requests

logger = logging.getLogger(__name__)

TAGSFILE = 'tagsfile.pkl'

class EchoLayer(YowInterfaceLayer):

    def __init__(self):
        super(EchoLayer, self).__init__()
        YowInterfaceLayer.__init__(self)
        self.connected = False
    	self.tagqueue = {}
    	self.stagetag = {}

        tagsfile = open(TAGSFILE, "rb")
        self.tagqueue = cPickle.load(tagsfile)
        tagsfile.close()


    def chitchatresponse(self, messageBody):

        chitchat_file = open('chitchat.pkl', 'rb')
        chitchat = cPickle.load(chitchat_file)
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

        lovequote_file = open('quotes.pkl', 'rb')
        lovequotes = cPickle.load(lovequote_file)
        lovequote_file.close()

        return random.choice(lovequotes)

    def gethelpstring(self):
        helpstring = "I do not understand that. You can try something like 'quote'"
        return helpstring


    def parsecapabilities(self, messageBody, phonenum):

        keyword = messageBody.split()[0]

        if keyword == "quote":
            return ('text', self.getquote())
        elif keyword == "name":
            return ('text', "Wait, I will soon have something cool")
        elif keyword == "img":
            image_number = messageBody.split()[1]
	    if image_number in ['1', '2', '3', '4', '5', '6', '7']:
            	return ('image', '/home/bitnami1/bhandara/website/img/t%s.jpg' % image_number )

        elif keyword == "savetag":
            keywords = messageBody.split()
            if len(keywords) != 2:
                return ('text', 'Invalid SAVETAG')
            tagname = '#' + keywords[1].strip('#')
            if tagname in self.tagqueue.keys():
                return ('text', 'Invalid SAVETAG: Given tag already exists')

            self.stagetag[phonenum] = tagname
            return ('text', 'Please send the content for tag: ' + tagname)

        else:
            return ('text', self.gethelpstring())


    def genresponse(self, messageProtocolEntity):

        phonenum = messageProtocolEntity.getFrom(False)
        logging.info( phonenum)
        #logging.info( self.stagetag)
        if phonenum in self.stagetag.keys():
            tagname = self.stagetag[phonenum].lower()

            self.tagqueue[tagname] = copy(messageProtocolEntity)

            #backup the self.tagqueue pending
            output = open(TAGSFILE, 'wb')
            cPickle.dump(self.tagqueue, output)
            output.close()

            del self.stagetag[phonenum]

            return ('text', 'Successfully attached to tag:' + tagname)

        messagebody = messageProtocolEntity.getBody()
        keyword = messagebody.split()[0].lower()
        if keyword in self.tagqueue.keys():
            return ('readymade', self.tagqueue[keyword])

        if messageProtocolEntity.getType() == 'media':
            return ('text', 'no media messages are handled')

        if messageProtocolEntity.getType() == 'text':
            (restype, response) = self.parsecapabilities(messagebody, phonenum)
            return (restype, response)



    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):

        if messageProtocolEntity.getType() == 'text':
            #time.sleep(0.454)
            logging.info( messageProtocolEntity.getBody())



        (restype, response) = self.genresponse(messageProtocolEntity)

        if restype == 'image':
	    self.image_send(messageProtocolEntity.getFrom(), response )

        elif restype == 'text':
            if response != "" and response != "<no results>" and len(response) < 250:
                safe_response = response.encode('ascii','ignore')
                messageProtocolEntity.setBody(safe_response)
            elif len(messagebody.split(' ')) == 1:
                messageProtocolEntity.setBody(":)")
            else:
                messageProtocolEntity.setBody("Can I answer every question? Nobody likes a know-it-all!!!")

            self.onTextMessage(messageProtocolEntity)
            self.toLower(response.forward(messageProtocolEntity.getFrom()))

        elif response.getType() == 'media':
            self.onMediaMessage(response)
            self.toLower(response.forward(messageProtocolEntity.getFrom()))

        self.toLower(messageProtocolEntity.ack())
        self.toLower(messageProtocolEntity.ack(True))

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        self.toLower(entity.ack())

    def onTextMessage(self,messageProtocolEntity):
        logging.info(("Echoing %s to %s" % (messageProtocolEntity.getBody(), messageProtocolEntity.getFrom(False))))


    def onMediaMessage(self, messageProtocolEntity):
        if messageProtocolEntity.getMediaType() == "image":
            logging.info(("Echoing image %s to %s" % (messageProtocolEntity.url, messageProtocolEntity.getFrom(False))))

        elif messageProtocolEntity.getMediaType() == "location":
            logging.info(("Echoing location (%s, %s) to %s" % (messageProtocolEntity.getLatitude(), messageProtocolEntity.getLongitude(), messageProtocolEntity.getFrom(False))))

        elif messageProtocolEntity.getMediaType() == "vcard":
            logging.info(("Echoing vcard (%s, %s) to %s" % (messageProtocolEntity.getName(), messageProtocolEntity.getCardData(), messageProtocolEntity.getFrom(False))))


    @ProtocolEntityCallback("success")
    def onSuccess(self, entity):
        self.connected = True
        logger.info("Logged in! Auth")

    @ProtocolEntityCallback("failure")
    def onFailure(self, entity):
        self.connected = False
        logger.info("Login Failed, reason: %s" % entity.getReason())

    def image_send(self, number, path, caption = None):
            jid = self.normalizeJid(number)
            entity = RequestUploadIqProtocolEntity(RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE, filePath=path)
            successFn = lambda successEntity, originalEntity: self.onRequestUploadResult(jid, path, successEntity, originalEntity, caption)
            errorFn = lambda errorEntity, originalEntity: self.onRequestUploadError(jid, path, errorEntity, originalEntity)

            self._sendIq(entity, successFn, errorFn)



    def normalizeJid(self, number):
        if '@' in number:
            return number
        elif "-" in number:
            return "%s@g.us" % number

        return "%s@s.whatsapp.net" % number

    ########### callbacks ############

    def onRequestUploadResult(self, jid, filePath, resultRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity, caption = None):

        if requestUploadIqProtocolEntity.mediaType == RequestUploadIqProtocolEntity.MEDIA_TYPE_AUDIO:
            doSendFn = self.doSendAudio
        else:
            doSendFn = self.doSendImage

        if resultRequestUploadIqProtocolEntity.isDuplicate():
            doSendFn(filePath, resultRequestUploadIqProtocolEntity.getUrl(), jid,
                             resultRequestUploadIqProtocolEntity.getIp(), caption)
        else:
            successFn = lambda filePath, jid, url: doSendFn(filePath, url, jid, resultRequestUploadIqProtocolEntity.getIp(), caption)
            mediaUploader = MediaUploader(jid, self.getOwnJid(), filePath,
                                      resultRequestUploadIqProtocolEntity.getUrl(),
                                      resultRequestUploadIqProtocolEntity.getResumeOffset(),
                                      successFn, self.onUploadError, self.onUploadProgress, async=False)
            mediaUploader.start()

    def onRequestUploadError(self, jid, path, errorRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity):
        logger.error("Request upload for file %s for %s failed" % (path, jid))

    def onUploadError(self, filePath, jid, url):
        logger.error("Upload file %s to %s for %s failed!" % (filePath, url, jid))

    def onUploadProgress(self, filePath, jid, url, progress):
	return
        #sys.stdout.write("%s => %s, %d%% \r" % (os.path.basename(filePath), jid, progress))
        #sys.stdout.flush()


    def doSendImage(self, filePath, url, to, ip = None, caption = None):
        entity = ImageDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to, caption = caption)
        self.toLower(entity)

    def doSendAudio(self, filePath, url, to, ip = None, caption = None):
        entity = AudioDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to)
        self.toLower(entity)

