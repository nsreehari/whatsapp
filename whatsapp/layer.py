from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_media.protocolentities import RequestUploadIqProtocolEntity, ImageDownloadableMediaMessageProtocolEntity, AudioDownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_media.mediauploader import MediaUploader 
from yowsup.layers.protocol_media.mediadownloader import MediaDownloader 
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity 

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

class EchoLayer(YowInterfaceLayer):

    def __init__(self):
        super(EchoLayer, self).__init__()
        YowInterfaceLayer.__init__(self)
        self.connected = False
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
            tagname = '#' + keywords[1].strip('#')
            if tagname in self.tagqueue.keys():
                return ('text', 'Invalid SAVETAG: Given tag already exists')

            self.stagetag[phonenum] = tagname
            return ('text', 'Please send the content for tag: ' + tagname)

        elif keyword == "updatetag":
            keywords = messageBody.split()
            if len(keywords) != 2:
                return ('text', 'Invalid tag')
            tagname = '#' + keywords[1].strip('#')
            if tagname not in self.tagqueue.keys():
                return ('text', 'Invalid UPDATE TAG: Given tag does not exist')

            self.stagetag[phonenum] = tagname
            return ('text', 'Please send the content for tag: ' + tagname)
        else:
            return ('text', self.gethelpstring())


    def genresponse(self, message):

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
            if keyword[0] == '#':
                   keyword = keyword[1:]
            if keyword in self.tagqueue.keys():
                   return ('readymade', self.tagqueue[keyword])

        if message.getType() == 'media':
            logger.info(self.getMediaMessageBody(message))    

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



    @ProtocolEntityCallback("message")
    def onMessage(self, recdMsg):

        if recdMsg.getType() == 'text':
            logging.info( recdMsg.getBody())

        (restype, response) = self.genresponse(recdMsg)

        if restype == 'image':
            self.image_send(recdMsg.getFrom(), response)

        elif restype == 'text':
            self.message_send(recdMsg.getFrom(), response)

        elif restype == 'readymade':
            self.logResponse(response)
            self.toLower(response.forward(recdMsg.getFrom()))

        self.toLower(recdMsg.ack())
        self.toLower(recdMsg.ack(True))

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        self.toLower(entity.ack())



    def logResponse(self, msg):
        if msg.getType() == 'text':
                logging.info(("Echoing %s to %s" % (msg.getBody(), msg.getFrom(False))))
        elif msg.getType() == 'media':
            if msg.getMediaType() == "image":
                logging.info(("Echoing image %s to %s" % (msg.url, msg.getFrom(False))))
            
            elif msg.getMediaType() == "location":
                logging.info(("Echoing location (%s, %s) to %s" % (msg.getLatitude(), msg.getLongitude(), msg.getFrom(False))))
            
            elif msg.getMediaType() == "vcard":
                logging.info(("Echoing vcard (%s, %s) to %s" % (msg.getName(), msg.getCardData(), msg.getFrom(False))))


    @ProtocolEntityCallback("success")
    def onSuccess(self, entity):
        self.connected = True
        logger.info("Logged in! Auth")

    @ProtocolEntityCallback("failure")
    def onFailure(self, entity):
        self.connected = False
        logger.info("Login Failed, reason: %s" % entity.getReason())


    def message_send(self, number, content):
            outgoingMessage = TextMessageProtocolEntity(content.encode("utf-8") if version_info >= (3,0) else content, to = self.normalizeJid(number))
            self.toLower(outgoingMessage)

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

    def getMediaMessageBody(self, message):
        if message.getMediaType() in ("image", "audio", "video"):
            return self.getDownloadableMediaMessageBody(message)
        else:
            return "[Media Type: %s]" % message.getMediaType()


    def getDownloadableMediaMessageBody(self, message):
         return "[Media Type:{media_type}, Size:{media_size}, URL:{media_url}]".format(
            media_type = message.getMediaType(),
            media_size = message.getMediaSize(),
            media_url = message.getMediaUrl()
            )


