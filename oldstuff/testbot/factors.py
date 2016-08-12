import sys
import random
import telepot
from telepot.delegate import per_chat_id, create_open

"""
$ python2.7 guess.py <token>

Guess a number:

1. Send the bot anything to start a game.
2. The bot randomly picks an integer between 0-99.
3. You make a guess.
4. The bot tells you to go higher or lower.
5. Repeat step 3 and 4, until guess is correct.
"""

class Player(telepot.helper.ChatHandler):
    def __init__(self, seed_tuple, timeout):
        super(Player, self).__init__(seed_tuple, timeout)
        self._answer = random.randint(1,99)

    def _hint(self, answer, m1, m2):
        return 'Wrong! %s * %s is not equal to %s. Please give correct answer ' % (m1, m2, answer)

    def open(self, initial_msg, seed):
        self.sender.sendMessage('Guess the factors of the number - %s' % self._answer)
        return True  # prevent on_message() from being called on the initial message

    def on_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance2(msg)

        if content_type != 'text':
            self.sender.sendMessage('Give me two numbers, please.')
            return

        try:
            m = msg['text'].strip().split()
            m1 = int(m[0])
            m2 = int(m[1])
            if len(m) > 2:
                raise ValueError
        except :
            self.sender.sendMessage('Give two numbers correctly, please.')
            return

        # check the guess against the answer ...
        if m1 * m2 != self._answer:
            # give a descriptive hint
            hint = self._hint(self._answer, m1, m2)
            self.sender.sendMessage(hint)
        else:
            self.sender.sendMessage('Correct!')
            self.close()

    def on_close(self, exception):
        if isinstance(exception, telepot.helper.WaitTooLong):
            self.sender.sendMessage('Game expired. Be quick with the answer next time ' )


TOKEN = sys.argv[1]

bot = telepot.DelegatorBot(TOKEN, [
    (per_chat_id(), create_open(Player, timeout=10)),
])
bot.notifyOnMessage(run_forever=True)


