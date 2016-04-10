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
    _start_keyboard = {'keyboard':  [['Start']]}
    _show_keyboard = {'keyboard': [['10','20', '50'], ['100','500', '1000'], ['Cancel', 'Done']]}
    def __init__(self, seed_tuple, timeout):
        super(Player, self).__init__(seed_tuple, timeout)
        self._answer = random.randint(1,199) * 10
        self._fsm = ''

    def formatfsm(self):
        a = {}
        for i in self._fsm.split():
            if i in a.keys():
                a[i] += 1
            else:
                a[i] = 1
        return '  '.join(map(lambda i: '%sx%s' % (i, a[i]), a.keys()))

    def _hint(self, answer, sum):
        return 'Wrong! The given notes add up to %s, which is not equal to %s. Please give correct answer ' % (sum, answer)

    def open(self, initial_msg, seed):

        self.sender.sendMessage('Give the notes denomination for Rs.%s' % self._answer, reply_markup=self._show_keyboard )
        return True  # prevent on_message() from being called on the initial message

    def on_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance2(msg)

        if content_type != 'text':
            self.sender.sendMessage('Give me valid note denominations only, please.')
            return

        if msg['text'].strip() == 'Cancel':
            self.sender.sendMessage('Game cancelled.', reply_markup=self._start_keyboard  )
            self.close()
            return 

        if msg['text'].strip() == 'Done':
            sum = 0
            for i in self._fsm.split():
                x = int(i)
                sum += x

            # check the guess against the answer ...
            if sum != self._answer:
                # give a descriptive hint
                hint = self._hint(self._answer, sum)
                self.sender.sendMessage(hint)
            else:
                self.sender.sendMessage('Correct!', reply_markup=self._start_keyboard )
                self.close()

        try:
            m = msg['text'].strip().split()
            if m[0] != 'Done':
                x = int(m[0])
                if x not in [ 10, 20, 50, 100, 500, 1000 ]:
                    raise ValueError
                #self.sender.sendMessage('Game cancelled.', reply_markup=self._start_keyboard  )
                self._fsm = self._fsm + ' ' + msg['text'].strip()
                self.sender.sendMessage('Target: Rs. %s   Notes added: %s' % (self._answer, self.formatfsm()))
                return


        except :
            self.sender.sendMessage('Give me valid note denominations, please')
            return


    def on_close(self, exception):
        if isinstance(exception, telepot.helper.WaitTooLong):
            self.sender.sendMessage('Game expired. Be quick with the answer next time ', reply_markup=self._start_keyboard  )


TOKEN = sys.argv[1]

bot = telepot.DelegatorBot(TOKEN, [
    (per_chat_id(), create_open(Player, timeout=150)),
])
bot.notifyOnMessage(run_forever=True)


