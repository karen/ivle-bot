import os
import asyncio
import random
import telepot
import telepot.async
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardHide, ForceReply
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import InlineQueryResultArticle, InlineQueryResultPhoto, InputTextMessageContent
import ivle_bot_helper as helper
import models
from models import User, Module

class IVLEBot(telepot.async.Bot):
    def __init__(self, *args, **kwargs):
        super(IVLEBot, self).__init__(*args, **kwargs)
        self._answerer = telepot.async.helper.Answerer(self)
        self._message_with_inline_keyboard = None

    async def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        user_first_name = msg['from']['first_name']
        try:
            user = User.get(user_id=chat_id)
        except User.DoesNotExist:
            user = User(user_id=chat_id)

        # text only for now
        if content_type != 'text':
            return
        
        # process params
        content = msg['text'].split()
        command = content[0]
        params = content[1:]
        print('{} # {} # {}'.format(content, command, params))

        if command[0] != '/' and not user.auth_token:
            await self.sendMessage(chat_id,
                'Please authenticate by logging in to IVLE and sending me your token. [/help]')
        
        if command == '/help':
            await self.sendMessage(chat_id,
                'To get started, please get a token by logging in to IVLE: /login and send it to me: /setup <token>.')
        elif command == '/login':
            login_params = {'api_key': helper.API_KEY, 'chat_id': chat_id}
            markup = InlineKeyboardMarkup(inline_keyboard=[
                         [dict(text='Login to IVLE',
                            url='https://ivle.nus.edu.sg/api/login/?apikey={api_key}'.format(**login_params))]])
            message = 'Hi {}! To get started, log in to IVLE with the link below.'.format(user_first_name)

            self._message_with_inline_keyboard = await self.sendMessage(chat_id,
                                                    message, reply_markup=markup)
            await self.sendMessage(chat_id,
                'When you are successfully redirected, copy the generated token and run /setup <token>.')
        elif command == '/setup':
            if not params:
                await self.sendMessage(chat_id, 'Usage: /setup <token>')
            else:
                token = params[0]
                success = False
                if user is not None:
                    u_result, success = await helper.do(token, helper.setup_user,
                        {'user': user, 'auth_token': token})
                if success:
                    await self.sendMessage(chat_id, 'I\'ll set up your modules now...')
                    m_result, success = await helper.do(token, helper.setup_modules, {'user': chat_id})       
                    await self.sendMessage(chat_id, m_result)
                else:
                    await self.sendMessage(chat_id,
                        'I\'m sorry, something went wrong setting up your token. :c')
        elif command == '/gradebook':
            if not params or len(params) > 1:
                await self.sendMessage(chat_id,
                    'Usage: /gradebook <module>')
            else:
                module_code = params[0]
                await self.sendMessage(chat_id,
                    'Hold on, I\'m checking your grades for {}...'.format(module_code))
                try:
                    module_id = Module.select(Module.module_id). \
                    where(Module.module_code.contains(module_code)). \
                    order_by(Module.acad_year.desc(), Module.semester.desc()). \
                    get().module_id
                except Module.DoesNotExist:
                    module_id = None

                if module_id is not None:
                    result, _ = await helper.do(user.auth_token, helper.get_gradebook, {
                        'module_code': module_code, 'module_id': module_id})
                else:
                    result = 'Hmm, have you executed the /setup command? (You must also be taking the module {}. 😶)'.format(module_code)
                await self.sendMessage(chat_id, result)
        elif command == '/timetable':
            if not params:
                await self.sendMessage(chat_id,
                    'Usage: /timetable <module1> <module2> ...')
            else:
                modules = params
                await self.sendMessage(chat_id,
                    'Hold on, I\'m checking your timetable for {}...'.format(
                        ', '.join(map(lambda m: str(m), modules))))

                try:
                    module_ids = []
                    for module_code in modules:
                        module_id = Module.select(Module.module_id). \
                        where(Module.module_code.contains(module_code)). \
                        order_by(Module.acad_year.desc(), Module.semester.desc()). \
                        get().module_id
                        module_ids.append(module_id)
                except:
                    module_ids = []
                if module_ids:
                    result, _ = await helper.do(user.auth_token,
                        helper.get_timetable, {'modules': module_ids})
                else:
                    result = 'Sorry, something went wrong retrieving your timetable. 🙁'
                await self.sendMessage(chat_id, result)
        elif command == '/examtime':
            if not params:
                await self.sendMessage(chat_id, 'Usage: /examwhen? <module1> <module2> ...')
            else:
                modules = params
                await self.sendMessage(chat_id,
                    'Hold on, I\'m checking the exam timetable for {}...'.format(
                        ', '.join(map(lambda m: str(m), modules))))
                try:
                    module_ids = []
                    for module_code in modules:
                        module_ids.append(Module.select(Module.module_id). \
                            where(Module.module_code.contains(module_code)). \
                            order_by(Module.acad_year.desc(), Module.semester.desc()). \
                            get().module_id)
                except:
                    module_ids = []

                if module_ids:
                    result, _ = await helper.do(user.auth_token, helper.get_exam_timetable, {'modules': module_ids})
                else:
                    result = 'Hmm, have you executed the /setup command? (Please also check that you have spelled each module code correctly.)'
                await self.sendMessage(chat_id, result) 
        elif command == '/nextclass':
            if params:
                await self.sendMessage(chat_id, 'Usage: /nextclass')
            else:
                result, _ = await helper.do(user.auth_token, helper.get_next_class)
                await self.sendMessage(chat_id, result)
        elif command == '/announcements':
            if len(params) == 2:
                result, _ = await helper.do(user.auth_token, helper.get_recent_ann, {
                    'module_code': params[0], 'count': int(params[1])})
                await self.sendMessage(chat_id, result)
            elif not params:
                result, _ = await helper.do(user.auth_token, helper.get_unread_ann)
                await self.sendMessage(chat_id, result)
            else:
                await self.sendMessage(chat_id,
                    'Usage: /announcements for unread announcements, /announcements <module> <x> to retrieve the x most recent announcements')
        elif command == 'classestomorrow':
            if params:
                await self.sendMessage(chat_id, 'Usage: /classestomorrow')
            else:
                result, _ = await helperdo(user.auth_token, helper.get_classes_tomorrow)
                await self.sendMessage(chat_id, result)
        elif command == 'credits':
            await self.sendMessage(chat_id,
                'IVLE API: https://goo.gl/zav5bb\nIVLE API Wrapper: https://github.com/benjaminheng/pyivle\nMade because I was lazy and why not?')
        elif command == 'disclaimer':
            DISCLAIMER = 'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.'
            await self.sendMessage(chat_id, DISCLAIMER)
        else:
            p = random.random()
            message1 = 'Be content with what you have; rejoice in the way things are. When you realize there is nothing lacking, the whole world belongs to you.'
            message2 = 'Nature does not hurry, yet everything is accomplished.'
            message = message1 if p > 0.5 else message2
            await self.sendMessage(chat_id, message)

TOKEN = os.environ['BOT_TOKEN']  # get token from BOT_TOKEN variable

bot = IVLEBot(TOKEN)
loop = asyncio.get_event_loop()
loop.set_debug(True)

loop.create_task(bot.message_loop())
print('Listening ...')

loop.run_forever()