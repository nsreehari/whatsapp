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
 
    logger.info( ret)
    for (restype,response) in ret: 
    
      logger.info(  '%s: Send to %s %s ' % (datetime.now(), phonenum, restype))
      fns = { 
          'image': lambda path: bot.sendPhoto(phonenum, photo=path),
          'audio': lambda path: bot.sendAudio(phonenum, audio=path),
          'voice': lambda path: bot.sendVoice(phonenum, voice=path),
          'video': lambda path: bot.sendVideo(phonenum, video=path),
          'document': lambda path: bot.sendDocument(phonenum, document=path),
          'text': lambda response: bot.sendMessage(phonenum, text=response),
          'location': lambda response: bot.sendLocation(phonenum, latitude=response['lat'], longitude=response['long']),
      }
      fnw = lambda path: fns[restype](path)

      if restype in [ 'image' , 'audio', 'video', 'document', 'voice' ]:
          
          if 'cacheinfo' in response.keys():
                 path = response['cacheinfo']
                 M = fnw(path)
                 continue
          
          else:
              if 'localfile' in response.keys():
                 path = response['localfile']
                 M = fnw(open(path, 'rb'))
                 continue
              else:
                 path = response['mediaurl']
                 M = fnw(path)
                 continue

      elif restype in [ 'text', 'location' ]:
          M = fnw(response)
          continue


def echo(bot, update):
    jsondict = {'medium': 'telegram'}
    jsondict['phonenum'] = update.message.chat_id
    if update.message.text:
        jsondict['msgtype'] = 'text'
        jsondict['msgbody'] = update.message.text

    elif update.message.location:
        jsondict['msgtype'] = 'media'
        jsondict['mediatype'] = 'location'
        jsondict['lat'] = update.message.location.latitude
        jsondict['long'] = update.message.location.longitude
        jsondict['name'] = ""
        jsondict['url'] = ""
        jsondict['encoding'] = "raw"

    elif update.message.contact:
        jsondict['msgtype'] = 'media'
        jsondict['mediatype'] = 'contact'
        jsondict['carddata'] = update.message.contact.phone_number
        jsondict['name'] = update.message.contact.first_name

    elif update.message.photo :# or update.message.video or update.message.audio or update.message.voice or update.message.document :
        jsondict['msgtype'] = 'media'

        if update.message.photo:
            jsondict['mediatype'] = 'image'
            fileloc = bot.getFile(file_id=update.message.photo[-1].file_id)
        elif update.message.video:
            jsondict['mediatype'] = 'video'
            fileloc = bot.getFile(file_id=update.message.video.file_id)
        elif update.message.audio:
            jsondict['mediatype'] = 'audio'
            fileloc = bot.getFile(file_id=update.message.audio.file_id)
        elif update.message.voice:
            jsondict['mediatype'] = 'voice'
            fileloc = bot.getFile(file_id=update.message.voice.file_id)
        elif update.message.document:
            jsondict['mediatype'] = 'document'
            fileloc = bot.getFile(file_id=update.message.document.file_id)

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


