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
import json, sys


BOTKEY = "159172493:AAFHWyVInl7j4WTtOQAeHnvhE4FSyyZagYI"
if not BOTKEY:
    try:
        BOTKEY = sys.argv[1]
    except:
        print "BOTKEY not provided"
        sys.exit()

# Enable logging
logging.basicConfig(filename="/tmp/telegram_mgmt.log",
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    bot.sendMessage(update.message.chat_id, text='Hi!')

from subprocess import call
def restart(bot, update):
    bot.sendMessage(update.message.chat_id, text='Restarting')
    call("/home/bitnami1/whatsapp/telegram_ctl.sh gitupdate".strip().split())
    
    outp  =''.join(open("/tmp/Xrestart.log"))
    bot.sendMessage(update.message.chat_id, text=outp)
    bot.sendMessage(update.message.chat_id, text='Done!')

def tstatus(bot, update):
    call("/home/bitnami1/whatsapp/telegram_ctl.sh status".strip().split())
    outp  =''.join(open("/tmp/Xrestart.log"))
    bot.sendMessage(update.message.chat_id, text=outp)

def tstop(bot, update):
    call("/home/bitnami1/whatsapp/telegram_ctl.sh stop".strip().split())
    outp  =''.join(open("/tmp/Xrestart.log"))
    bot.sendMessage(update.message.chat_id, text=outp)

def tstart(bot, update):
    call("/home/bitnami1/whatsapp/telegram_ctl.sh start".strip().split())
    outp  =''.join(open("/tmp/Xrestart.log"))
    bot.sendMessage(update.message.chat_id, text=outp)

def help(bot, update):
    bot.sendMessage(update.message.chat_id, text='Help!')

def echo(bot, update):
    bot.sendMessage(update.message.chat_id, text=update.message.text)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(BOTKEY)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.addTelegramCommandHandler("start", start)
    dp.addTelegramCommandHandler("gitupdate", restart)
    dp.addTelegramCommandHandler("tstart", tstart)
    dp.addTelegramCommandHandler("tstop", tstop)
    dp.addTelegramCommandHandler("tstatus", tstatus)
    dp.addTelegramCommandHandler("help", help)

    # on noncommand i.e message - echo the message on Telegram
    dp.addTelegramMessageHandler(echo)

    # log all errors
    dp.addErrorHandler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()


