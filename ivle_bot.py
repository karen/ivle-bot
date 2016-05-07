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
        print('Chat:', content_type, chat_type, chat_id)
        print(msg)
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

        if command[0] != '/' and not user.auth_token:
            await self.sendMessage(chat_id, 'Remember to authenticate by logging in to IVLE and sending me your token.')
        
        if command == '/help':
            await self.sendMessage(chat_id, 'Well, hello there. You must be lost. I am IVLEBot.')
            await self.sendMessage(chat_id, 'To get started, you need to log in to IVLE.')
            await self.sendMessage(chat_id, 'You will receive a token which I require. Please send it to me using /setup <token>.')
            await self.sendMessage(chat_id, 'If you are unsure of a command, simply enter it and I will tell you more about it\'s usage')
        elif command == '/login':
            login_params = {'api_key': helper.API_KEY, 'chat_id': chat_id}
            markup = InlineKeyboardMarkup(inline_keyboard=[
                         [dict(text='Login to IVLE', url='https://ivle.nus.edu.sg/api/login/?apikey={api_key}'.format(**login_params))]])
            message = 'Hi {}! To get started, log in to IVLE with the link below.'.format(user_first_name)

            self._message_with_inline_keyboard = await self.sendMessage(chat_id, message, reply_markup=markup)
            await self.sendMessage(chat_id, 'When you are successfully redirected, copy the really long token (e.g. "FEAF9E5...") and run /setup FEAF9E5...')
            await self.sendMessage(chat_id, 'By the way, do not share this token with friends, family, or pets.')
        elif command == '/setup':
            if not params:
                await self.sendMessage(chat_id, 'Usage: /setup <token>')
            else:
                token = params[0]
                success = False
                if user is not None:
                    # validate
                    u_result, success = await helper.do(token, helper.setup_user, {'user': chat_id, 'auth_token': token})
                    await self.sendMessage(chat_id, u_result)

                # validation succeeded
                if success:
                    await self.sendMessage(chat_id, 'I\'ll set up your modules now...')
                    m_result, success = await helper.do(token, helper.setup_modules, {'user': chat_id})       
                    await self.sendMessage(chat_id, m_result)
        elif command == '/gradebook':
            if not params or len(params) > 1:
                await self.sendMessage(chat_id, 'Usage: /gradebook <module>')
            else:
                module_code = params[0]
                await self.sendMessage(chat_id, 'Hold on, I\'m checking your grades for {}...'.format(module_code))

                try:
                    module_id = Module.select(Module.module_id).where(Module.module_code== module_code).order_by(Module.acad_year.desc(), Module.semester.desc()).get().module_id
                except Module.DoesNotExist:
                    module_id = None

                if module_id is not None:
                    result, _ = await helper.do(user.auth_token, helper.get_gradebook, {'module_code': module_code, 'module_id': module_id})
                else:
                    result = 'Hmm, have you executed the /setup command? (You must also be taking the module {}.)'.format(module_code)
                await self.sendMessage(chat_id, result)
        elif command == '/timetable':
            if not params:
                await self.sendMessage(chat_id, 'Usage: /timetable <module1> [, <module2>, ...]')
            else:
                modules = params
                await self.sendMessage(chat_id, 'Hold on, I\'m checking your timetable for {}...'.format(', '.join(map(lambda m: str(m), modules))))

                try:
                    module_ids = []
                    for code in modules:
                        module_ids.append(module_id = Module.select(Module.module_id).where(Module.module_code== module_code).order_by(Module.acad_year.desc(), Module.semester.desc()).get().module_id)
                except:
                    module_ids = None

                if module_ids is not None:
                    result, _ = await helper.do(user.auth_token, helper.get_timetable, {'modules': module_ids})
                else:
                    result = 'Hmm, have you executed the /setup command? (Please also check that you have spelled each module code correctly.'
                await self.sendMessage(chat_id, result)
        elif command == '/examtime':
            if not params:
                await self.sendMessage(chat_id, 'Usage: /examwhen? <module1> [, <module2>, ...]')
            else:
                modules = params
                await self.sendMessage(chat_id, 'Hold on, I\'m checking the exam timetable for {}...'.format(', '.join(map(lambda m: str(m), modules))))
                try:
                    module_ids = []
                    for code in modules:
                        module_ids.append(module_id = Module.select(Module.module_id).where(Module.module_code== module_code).order_by(Module.acad_year.desc(), Module.semester.desc()).get().module_id)
                except:
                    module_ids = None

                if module_ids is not None:
                    result, _ = await helper.do(user.auth_token, helper.get_exam_timetable, {'modules': module_ids})
                else:
                    result = 'Hmm, have you executed the /setup command? (Please also check that you have spelled each module code correctly.'
                await self.sendMessage(chat_id, result) 
        elif command == '/nextclass':
            if params:
                await self.sendMessage(chat_id, 'Usage: /nextclass')
            else:
                result, _ = await helper.do(user.auth_token, helper.get_next_class, {'user': user.user_id})
                await self.sendMessage(chat_id, result)
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