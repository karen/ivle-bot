import os
import asyncio
import random
import telepot
import telepot.async
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardHide, ForceReply
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import InlineQueryResultArticle, InlineQueryResultPhoto, InputTextMessageContent
import ivle_bot_helper as helper
from models import User, Module
import userstr

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
            user = User.create(user_id=chat_id, auth_token='')
        user.save()

        # text only for now
        if content_type != 'text':
            return
        
        # process params
        content = msg['text'].split()
        command = content[0]
        params = content[1:]

        if command[0] != '/' and not user.auth_token:
            await self.sendMessage(chat_id,
                userstr.authenticate)
        if command == '/help':
            await self.sendMessage(chat_id,
                userstr.help)
            await self.sendMessage(chat_id,
                userstr.helpcmd)
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
                u_result, success = await helper.do(token, helper.setup_user,
                        {'user': user, 'auth_token': token})
                await self.sendMessage(chat_id, u_result)
                if not success:
                    return
                await self.sendMessage(chat_id, userstr.setup_true)
                m_result, success = await helper.do(token, helper.setup_modules)
                await self.sendMessage(chat_id, m_result)
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
                    result = userstr.module_ids_not_found
                await self.sendMessage(chat_id, result)
        elif command == '/examtime':
            if not params:
                await self.sendMessage(chat_id, 'Usage: /examtime <module1> <module2> ...')
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
                    result = userstr.module_ids_not_found
                await self.sendMessage(chat_id, result) 
        elif command == '/nextclass':
            if params:
                await self.sendMessage(chat_id, 'Usage: /nextclass')
            else:
                await self.sendMessage(chat_id, userstr.nextclass_wait)
                result, _ = await helper.do(user.auth_token, helper.get_next_class)
                await self.sendMessage(chat_id, result)
        elif command == '/announcements':
            if len(params) == 2:
                await self.sendMessage(chat_id, userstr.recent_ann_wait.format(params[0]))
                result, _ = await helper.do(user.auth_token, helper.get_recent_ann, {
                    'module_code': params[0], 'count': int(params[1])})
                await self.sendMessage(chat_id, result)
            elif not params:
                await self.sendMessage(chat_id, userstr.unread_ann_wait)
                results, _ = await helper.do(user.auth_token, helper.get_unread_ann)
                if type(results) == str:
                    await self.sendMessage(chat_id, results)
                else:
                    for k, v in results.items():
                        await self.sendMessage(chat_id, "You\'ve not read these announcements from {}:\n".format(k))
                        await self.sendMessage(chat_id, v)
            else:
                await self.sendMessage(chat_id,
                    'Usage: /announcements for unread announcements, /announcements <module> <x> to retrieve the x most recent announcements')
        elif command == '/classestomorrow':
            if params:
                await self.sendMessage(chat_id, 'Usage: /classestomorrow')
            else:
                await self.sendMessage(chat_id, userstr.classes_tomorrow_wait)
                result, _ = await helper.do(user.auth_token, helper.get_classes_tomorrow)
                await self.sendMessage(chat_id, result)
        elif command == '/credits':
            await self.sendMessage(chat_id, userstr.credits)
        elif command == '/disclaimer':
            await self.sendMessage(chat_id, userstr.disclaimer)
        else:
            p = random.random()
            message = userstr.fortune1 if p > 0.5 else userstr.fortune2
            await self.sendMessage(chat_id, message)

TOKEN = os.environ['BOT_TOKEN']  # get token from BOT_TOKEN variable

bot = IVLEBot(TOKEN)
loop = asyncio.get_event_loop()
loop.set_debug(True)

loop.create_task(bot.message_loop())
print('Listening ...')

loop.run_forever()