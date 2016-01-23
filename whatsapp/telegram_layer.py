#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages
# This program is dedicated to the public domain under the CC0 license.

"""
This Bot uses the Updater class to handle the bot.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram import Updater
import logging
import json
from datetime import datetime
from urllib import urlretrieve
from os import unlink
from os.path import isfile, basename
from copy import copy, deepcopy

from azure.storage.blob import BlobService
from mimetypes import guess_type

from serve_azure import serve, runloop



# Enable logging
logging.basicConfig(filename="/tmp/telegram.log",
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

logger = logging.getLogger(__name__)


ACCOUNT = 'msgtest'
CONTAINER = 'telegram'

blob_service = BlobService(account_name='msgtest', account_key='sJQjZXgR/IUH4o4/CmbXue3DGxRgwkzy0SILxJMSgmd26lFCXUdqrtwwjmEPU9CrcIvoJG3yv6L0R55o9BqnXw==')

blob_service.create_container(CONTAINER, x_ms_blob_public_access='container')


def uploadblob(fileidshort, mediaurl):
    global ACCOUNT
    fileid = fileidshort + basename(mediaurl)
    tmppath = '/tmp/' + fileid
    urlretrieve(mediaurl, tmppath)
    blob_service.put_block_blob_from_path(
        CONTAINER,
        fileid,
        tmppath,
        x_ms_blob_content_type=guess_type(tmppath)
    )
    return 'https://%s.blob.core.windows.net/%s/%s' %(ACCOUNT, CONTAINER, fileid)



def downloadblob (fileid, filename): 
    blob_service.get_blob_to_path(
        CONTAINER,
        fileid,
        filename
    )


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Hi!')


def help(bot, update):
    bot.sendMessage(update.message.chat_id, text='Help!')


def send_message(bot, sendmsg):
            
            jsondict = json.loads(sendmsg)
            phonenum = jsondict['phonenum']
            if jsondict['restype'] == 'list':
                ret = jsondict['response']
            else:
                ret = [(jsondict['restype'], jsondict['response'])]
 

            for (restype,response) in ret: 
         
              logger.info(  '%s: Send to %s %s ' % (datetime.now(), phonenum, restype))
              if restype in [ 'image' , 'audio', 'video' ]:
                if 'localfile' in response.keys():
                     path = response['localfile']
                elif 'cacheinfo' in response.keys():
                     path = response['cacheinfo']
                     M = bot.sendPhoto(phonenum, photo=path)
                     return
                else:
                     mediaurl = response['mediaurl']
                     path = '/tmp/' + basename(mediaurl)
                     if isfile(path):
                         unlink(path)
                     urlretrieve(mediaurl, path)

                if isfile(path):
                  if restype == 'image':
                    M = bot.sendPhoto(phonenum, photo=path)
                  if restype == 'video':
                    #  self.video_send(phonenum, path, response['caption'])
                    # video not supported yet
                    self.message_send(phonenum, "Video Message not supported yet")
                    
                  if restype == 'audio':
                    # self.audio_send(phonenum, path)
                    # video not supported yet
                    self.message_send(phonenum, "Audio Message not supported yet")
                  unlink(path)

              elif restype == 'text':
                bot.sendMessage(phonenum, text=response)
              elif restype == 'vcard':
                self.vcard_send(phonenum, response['name'],response['carddata'])
              elif restype == 'location':
                self.location_send(phonenum, response['lat'],response['long'],
                       response['name'], response['url'], response['encoding'])


def echo(bot, update):
    jsondict = {'medium': 'telegram'}
    jsondict['phonenum'] = update.message.chat_id
    if update.message.text:
        jsondict['msgtype'] = 'text'
        jsondict['msgbody'] = update.message.text

    elif update.message.photo:
        jsondict['msgtype'] = 'media'
        jsondict['mediatype'] = 'image'

        fileloc = bot.getFile(file_id=update.message.photo[-1].file_id)
        jsondict['mediaurl'] = uploadblob(fileloc['file_id'], fileloc['file_path'])
        jsondict['cacheinfo'] = fileloc['file_id']
        jsondict['caption'] = None

    else:
        bot.sendMessage(update.message.chat_id, text="Unhandled Message Type")
        return
               

    pushjson = json.dumps(jsondict)
    if False: #AZURE_SERVICING:
            #msg = Message(pushjson)
            #self.bus_service.send_queue_message('process_incoming', msg)
            pass
    else:
            retjson = serve.getResponseWrapper(pushjson, '')
            if retjson:
                send_message(bot, retjson)




def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("135342801:AAFaninNSzDkYU8UzonHeOhcu5fVaPlCC7Y")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.addTelegramCommandHandler("start", start)
    dp.addTelegramCommandHandler("help", help)

    # on noncommand i.e message - echo the message on Telegram
    dp.addTelegramMessageHandler(echo)

    # log all errors
    dp.addErrorHandler(error)

    # Start the Bot
    updater.start_polling()

    runloop()
    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()


