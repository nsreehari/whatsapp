# Telegram Proxy Bot 

A simple BITM (bot-in-the-middle) for [Telegram](https://telegram.org/) acting as some kind of "proxy". You can use it as "virtual" second account for your purposes or to provide support for your bots without revealing your "real" nickname.  

## Prerequisites
* Python 3 (maybe works with Python 2, but I haven't tested it);
* [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI/) library;
* Telegram account.

## How to install
* Get your own bot's token from [@BotFather](https://telegram.me/botfather);
* Find out your account's unique ID (you can use my [My ID bot](https://telegram.me/my_id_bot) or just send message via Curl or something else and get `Message.chat.id` from response JSON);
* Fill in the necessary variables in `config.py`;
* Start bot: `python3 proxy_bot.py`


## How it works

The idea of this bot is pretty simple: you just place bot between you and the one you want to chat with. The upside is that no one will find out your unique chat id or some other info (nickname, first name or avatar, for example). They won't also know your last seen time. However, the downside is that you can't initiate chat with someone (Because you're writing from bot and bots can't start chats to prevent spam), so you'll have to ask people to write to your bot first.

![A simple scheme of interaction](https://habrastorage.org/files/4a2/d19/753/4a2d19753eb34073bfda0b872bf228b3.png)

![](http://i.imgur.com/PKheJam.png)


## Notes and restrictions

1. Message formatting (both Markdown and HTML) is disabled. You can easily add `parse_mode` argument to `send_message` function to enable it.
2. You should **always** use "reply" function, because bot will check `message_id` of selected "message to reply".
3. Storage is needed to save `"message_id":"user_id"` key-value pairs. First, I intended to delete `message_id` which I've already answered, but then I decided to remove this, so you can answer any message from certain user and multiple times.
4. Supported message types in reply: `text`, `sticker`, `photo`, `video`, `audio`, `voice`, `document`, `location`.

## Why did you do this?

Mostly for testing purposes while studying [Telegram Bot API](https://core.telegram.org/bots/api).  
I understand, that "proxy" bots can be used to prevent spammers from being reported, so if you encounter such bots that are used to do "bad" things, feel free to report them: [abuse@telegram.org](mailto:abuse@telegram.org)


## Contact
You can contact me via my [Proxy Bot](https://telegram.me/msg_proxy_bot). I can't ensure instant reply, but I'll do my best to answer your questions (if any) ASAP.# telebot
