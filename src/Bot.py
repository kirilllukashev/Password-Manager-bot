from DataBase import Database
from DataBase import sql
import telebot
import time
import asyncio
import sys


class Bot:
    START = 0
    SET_URL = 1
    SET_LOGIN = 2
    SET_PASSWORD = 3
    SET_DESCRIPTION = 4
    CHOOSE_URL = 5
    CHOOSE_TIME = 6

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.password_cnt = 0
        self.bot = telebot.TeleBot(
            self.api_key, parse_mode=None)
        self.host = sys.argv[2]
        self.user = sys.argv[3]
        self.password = sys.argv[4]
        self.data_base_name = sys.argv[5]
        self.data_base = Database(
            host=self.host, user=self.user,
            password=self.password, database=self.data_base_name)

        self.create_password_base()

        self.create_state_base()

        self.create_delete_base()

        self.create_time_table()

        self.messages = dict()
        with open("messages.json", "r") as file:
            self.messages = eval("".join(file.readlines()))

        @self.bot.message_handler(commands=["start"])
        def start_message(message: telebot.types.Message):
            msg = self.messages["start"]
            chat_id = message.from_user.id
            self.bot.send_message(
                chat_id, msg)
            self.data_base.REPLACE(
                self.state_table, self.state_cols,
                (chat_id, Bot.START, int(time.time())))
            self.data_base.REPLACE(
                self.time_table, self.time_cols,
                (chat_id, self.maximal_delay))

            self.start_message(chat_id)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_handler(call: telebot.types.CallbackQuery):
            chat_id = call.from_user.id
            if "start" in call.data:
                self.delete_messages(chat_id)
                self.start_message(chat_id)
                return

            if "add" in call.data:
                self.bot.answer_callback_query(
                    call.id, "Creating new password")
                self.add_password(call.from_user.id)
                return

            if "get" in call.data:
                self.bot.answer_callback_query(call.id, "Follow instructions")
                self.get_password(call.from_user.id)
                return

            if "setting" in call.data:
                self.bot.answer_callback_query(call.id, "Settings")
                self.settings(chat_id)
                return

            if "delete_time" in call.data:
                self.bot.answer_callback_query(
                    call.id, "Enter time in seconds")
                self.set_time(chat_id)
                return

            if "save" in call.data:
                self.bot.answer_callback_query(call.id, "Password saved")
                self.delete_messages(chat_id)
                self.start_message(chat_id)
                return

            if "choose_url" in call.data:
                self.bot.answer_callback_query(call.id, "URL chosen")
                self.delete_messages(chat_id)
                self.send_logins(chat_id, call.data.split()[1])
                return

            if "choose_login" in call.data:
                self.bot.answer_callback_query(call.id, "Login chosen")
                self.delete_messages(chat_id)
                self.send_passwords(chat_id, *(call.data.split()[1:]))
                return

            if "show" in call.data:
                self.bot.answer_callback_query(call.id, "Password shown")
                self.show_password(chat_id,
                                   call.message,
                                   call.data.split()[1],
                                   int(call.data.split()[2]))
                return

            pass_id = int(call.data.split()[1])

            if "edit" in call.data:
                self.bot.answer_callback_query(call.id, "Edit password")
                self.password_info(chat_id, pass_id)

            if "url" in call.data:
                self.bot.answer_callback_query(call.id, "Set password URL")
                self.set_url(chat_id, pass_id)

            if "login" in call.data:
                self.bot.answer_callback_query(call.id, "Set login")
                self.set_login(chat_id, pass_id)

            if "password" in call.data:
                self.bot.answer_callback_query(call.id, "Set password")
                self.set_password(chat_id, pass_id)

            if "description" in call.data:
                self.bot.answer_callback_query(call.id, "Set password")
                self.set_description(chat_id, pass_id)

            if "delete" in call.data:
                self.bot.answer_callback_query(call.id, "Password deleted")
                self.discard(chat_id, pass_id)

        @self.bot.message_handler(content_types=["text"])
        def message_getter(message: telebot.types.Message):
            chat_id = message.from_user.id
            self.save_message(message.id, chat_id)
            get = self.data_base.get_SELECT(
                Database.
                SELECT(("state", "pass_id")).
                FROM(self.state_table).
                WHERE("chat_id = {0}".format(chat_id)))
            if len(get) == 0:
                raise "WTF"

            state = get[0][0]
            pass_id = get[0][1]
            if state == Bot.START:
                self.delete_messages(chat_id)
                self.start_message(chat_id)
                return

            if state == Bot.CHOOSE_URL:
                self.send_urls(chat_id, message.text)
                return

            if state == Bot.CHOOSE_TIME:
                self.delete_messages(chat_id)
                self.take_time(chat_id, message.text)
                return

            row = self.data_base.get_SELECT(
                Database.
                SELECT(self.pass_cols).
                FROM(self.password_table).
                WHERE("pass_id IN ({})".format(pass_id)))[0]
            row = list(row)
            row = [i if i != None else 'None' for i in row]
            row[state + 1] = message.text
            self.data_base.REPLACE(
                self.password_table, self.pass_cols, tuple(row))

            self.delete_messages(chat_id)
            self.password_info(chat_id, pass_id)

    def create_password_base(self):
        self.password_table = "password_table"
        try:
            self.data_base.CREATE_TABLE(self.password_table,
                                        ("pass_id", "INT",
                                         "AUTO_INCREMENT"),
                                        ("chat_id", "INT"),
                                        ("url", "TEXT"),
                                        ("login", "TEXT"),
                                        ("password", "TEXT"),
                                        ("description", "TEXT"),
                                        ("timestamp", "INT"),
                                        ("PRIMARY", "KEY", "(pass_id)"))
        except (sql.errors.ProgrammingError) as err:
            if "exists" not in err.msg:
                raise err
        self.pass_cols = ("pass_id", "chat_id", "url", "login",
                          "password", "description", "timestamp")

    def create_state_base(self):
        self.state_table = "state_table"
        self.state_cols = ("chat_id", "state", "pass_id")
        try:
            self.data_base.CREATE_TABLE(self.state_table,
                                        ("chat_id", "INT", "UNIQUE"),
                                        ("state", "INT", "DEFAULT", "0"),
                                        ("pass_id", "INT", "DEFAULT", "0")
                                        )
        except (sql.errors.ProgrammingError) as err:
            if "exists" not in err.msg:
                raise err

    def create_delete_base(self):
        self.delete_table = "delete_table"
        self.delete_cols = ("message_id", "chat_id")
        try:
            self.data_base.CREATE_TABLE(self.delete_table,
                                        ("message_id", "INT"),
                                        ("chat_id", "INT"))
        except (sql.errors.ProgrammingError) as err:
            if "exists" not in err.msg:
                raise err

    def create_time_table(self):
        self.minimal_delay = 1
        self.maximal_delay = 86400
        self.time_table = "time_table"
        self.time_cols = ("chat_id", "time")
        try:
            self.data_base.CREATE_TABLE(
                self.time_table,
                ("chat_id", "INT", "UNIQUE"),
                ("time", "INT", "DEFAULT", "1000000000"))
        except (sql.errors.ProgrammingError) as err:
            if "exists" not in err.msg:
                raise err

    def add_password(self, chat_id):
        self.password_cnt += 1
        message_id = self.bot.send_message(
            chat_id, "Creating new password").id
        self.save_message(message_id, chat_id)
        self.data_base.REPLACE(
            self.password_table,
            ("chat_id", "timestamp"),
            (chat_id, time.time()))
        self.data_base.REPLACE(
            self.state_table,
            self.state_cols,
            (chat_id, Bot.START, self.password_cnt))

        self.password_info(chat_id, self.password_cnt)

    def password_info(self, chat_id, pass_id):
        self.delete_messages(chat_id)
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        button_url = telebot.types.InlineKeyboardButton(
            'Set URL', callback_data="url " + str(pass_id))
        button_login = telebot.types.InlineKeyboardButton(
            'Set login',  callback_data="login " + str(pass_id))
        button_password = telebot.types.InlineKeyboardButton(
            'Set password', callback_data="password " + str(pass_id))
        button_descr = telebot.types.InlineKeyboardButton(
            'Set description',  callback_data="description " + str(pass_id))
        button_finish = telebot.types.InlineKeyboardButton(
            'Save',  callback_data="save " + str(pass_id))
        button_discard = telebot.types.InlineKeyboardButton(
            'Delete', callback_data="delete " + str(pass_id))

        password_info = self.data_base.get_SELECT(Database.SELECT(
            self.pass_cols).FROM(
            self.password_table).WHERE("pass_id = {0}".format(pass_id)))

        if len(password_info) == 0:
            self.bot.send_message(chat_id, "This password is deleted.")
            return

        password_info = list(password_info[0])
        password_info[2:6] = [str(i) for i in password_info[2:6]]
        password_info = tuple(password_info)

        self.data_base.REPLACE(self.password_table,
                               self.pass_cols, password_info)

        markup.add(button_url, button_login, button_password,
                   button_descr, button_finish, button_discard)
        message = self.messages["pass_info"].format(*(password_info[2:6]))

        message_id = self.bot.send_message(
            chat_id, message, reply_markup=markup, parse_mode="HTML").id
        self.save_message(message_id, chat_id)

    def get_password(self, chat_id):
        id = self.bot.send_message(
            chat_id, "Send part of URL and choose.").id
        self.save_message(id, chat_id)
        self.data_base.REPLACE(
            self.state_table,
            ("chat_id", "state"),
            (chat_id, Bot.CHOOSE_URL))
        pass

    def start_message(self, chat_id):
        self.data_base.REPLACE(
            self.state_table,
            ("chat_id", "state"),
            (chat_id, Bot.START))
        self.delete_messages(chat_id)

        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        button_add = telebot.types.InlineKeyboardButton(
            'Add password', callback_data="add")
        button_get = telebot.types.InlineKeyboardButton(
            'Get password',  callback_data="get")
        button_settings = telebot.types.InlineKeyboardButton(
            'Settings', callback_data="settings")
        markup.add(button_add, button_get, button_settings)
        message_id = self.bot.send_message(
            chat_id, "Choose command:", reply_markup=markup).id
        self.save_message(message_id, chat_id)

    def set_url(self, chat_id, pass_id):
        message_id = self.bot.send_message(chat_id, "Set URL:").id
        self.save_message(message_id, chat_id)

        self.data_base.REPLACE(
            self.state_table,
            self.state_cols,
            (chat_id, Bot.SET_URL, pass_id))

    def set_login(self, chat_id, pass_id):
        message_id = self.bot.send_message(chat_id, "Set login:").id
        self.save_message(message_id, chat_id)

        self.data_base.REPLACE(
            self.state_table,
            self.state_cols,
            (chat_id, Bot.SET_LOGIN, pass_id))

    def set_password(self, chat_id, pass_id):
        message_id = self.bot.send_message(chat_id, "Set password:").id
        self.save_message(message_id, chat_id)

        self.data_base.REPLACE(
            self.state_table,
            self.state_cols,
            (chat_id, Bot.SET_PASSWORD, pass_id))

    def set_description(self, chat_id, pass_id):
        message_id = self.bot.send_message(chat_id, "Set description:").id
        self.save_message(message_id, chat_id)

        self.data_base.REPLACE(
            self.state_table,
            self.state_cols,
            (chat_id, Bot.SET_DESCRIPTION, pass_id))

    def discard(self, chat_id, pass_id):
        self.delete_messages(chat_id)
        self.data_base.DELETE(self.password_table,
                              "pass_id = {0}".format(pass_id))
        self.start_message(chat_id)

    def delete_messages(self, chat_id):
        get = self.data_base.get_SELECT(
            Database.
            SELECT(self.delete_cols).
            FROM(self.delete_table).
            WHERE("chat_id = {}".format(chat_id)))
        self.data_base.DELETE(
            self.delete_table, "chat_id = {}".format(chat_id))
        for row in get:
            try:
                self.bot.delete_message(row[1], row[0])
            except:
                pass

    def save_message(self, message_id, chat_id):
        self.data_base.REPLACE(
            self.delete_table, self.delete_cols, (message_id, chat_id))

    def send_urls(self, chat_id, url):
        get = self.data_base.get_SELECT(
            Database.
            SELECT(("url", )).
            FROM(self.password_table).
            WHERE("chat_id = {0} and url != 'None'".format(chat_id)).
            GROUP_BY(("url", )))
        urls = [i[0] for i in get if url in i[0]]
        msg = "{0} URLs found.".format(len(urls))

        if len(urls) == 0:
            id = self.bot.send_message(chat_id, msg).id
            self.save_message(id, chat_id)
            self.start_message(chat_id)
            return

        buttons = [telebot.types.InlineKeyboardButton(
            i, callback_data="choose_url " + i) for i in urls]
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(*buttons)
        id = self.bot.send_message(chat_id, msg, reply_markup=markup).id
        self.save_message(id, chat_id)

    def send_logins(self, chat_id, url):
        get = self.data_base.get_SELECT(
            Database.
            SELECT(("login", )).
            FROM(self.password_table).
            WHERE("chat_id = {0} AND url = '{1}'".format(chat_id, url)))
        logins = [i[0] for i in get]
        msg = "{0} logins found.".format(len(logins))
        buttons = [telebot.types.InlineKeyboardButton(
            i, callback_data="choose_login {0} {1}".format(i, url))
            for i in logins]
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(*buttons)
        id = self.bot.send_message(chat_id, msg, reply_markup=markup).id
        self.save_message(id, chat_id)

    def send_passwords(self, chat_id, login, url):
        get = self.data_base.get_SELECT(
            Database.
            SELECT(("pass_id", )).
            FROM(self.password_table).
            WHERE("chat_id = {0} AND url = '{1}' AND login = '{2}'".
                  format(chat_id, url, login)))
        for row in get:
            self.send_password_info(chat_id, row[0])

    def send_password_info(self, chat_id, pass_id):
        password_info = self.data_base.get_SELECT(
            Database.
            SELECT(("url", "login", "password", "description")).
            FROM(self.password_table).
            WHERE("pass_id = {0}".format(pass_id)))
        message = self.messages["send_pass_info"].format(*(password_info[0]))

        markup = telebot.types.InlineKeyboardMarkup(row_width=2)

        button_show = telebot.types.InlineKeyboardButton(
            "Show password",
            callback_data="show " + password_info[0][2] + " " + str(pass_id))
        markup.add(button_show)

        button_edit = telebot.types.InlineKeyboardButton(
            "Edit", callback_data="edit " + str(pass_id))
        markup.add(button_edit)

        message_id = self.bot.send_message(
            chat_id, message, reply_markup=markup, parse_mode="HTML").id
        self.start_message(chat_id)

    def show_password(self,
                      chat_id,
                      message: telebot.types.Message, password,
                      pass_id):
        password_info = self.data_base.get_SELECT(
            Database.
            SELECT(("url", "login", "password", "description")).
            FROM(self.password_table).
            WHERE("pass_id = {0}".format(pass_id)))
        text = self.messages["show_pass"].format(*(password_info[0]))

        markup = telebot.types.InlineKeyboardMarkup(row_width=2)

        button_edit = telebot.types.InlineKeyboardButton(
            "Edit", callback_data="edit " + str(pass_id))
        markup.add(button_edit)

        message_id = self.bot.edit_message_text(
            text, chat_id, message.id,
            reply_markup=markup, parse_mode="HTML").id
        time = self.get_time(chat_id)

        async def setTimeout(time):
            await asyncio.sleep(time)
            try:
                self.bot.delete_message(chat_id, message_id)
            except:
                pass

        asyncio.run(setTimeout(time))

        self.start_message(chat_id)

    def settings(self, chat_id):
        message = "Choose setting"
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        button_delete_time = telebot.types.InlineKeyboardButton(
            "Message delete delay", callback_data="delete_time")
        markup.add(button_delete_time)
        self.bot.send_message(chat_id, message, reply_markup=markup)

    def set_time(self, chat_id):
        get = self.data_base.get_SELECT(Database.SELECT(("time", )).FROM(
            self.time_table).WHERE("chat_id = {0}".format(chat_id)))
        time = get[0][0]
        id = self.bot.send_message(chat_id,
                                   self.messages["set_time"].
                                   format(time, self.minimal_delay, self.maximal_delay)).id
        self.save_message(id, chat_id)
        self.data_base.REPLACE(
            self.state_table,
            ("chat_id", "state"),
            (chat_id, Bot.CHOOSE_TIME))

    def take_time(self, chat_id, text: str):
        if not text.isdigit():
            id = self.bot.send_message("Not a number. Try again.").id
            self.save_message(id)
            self.set_time(chat_id)
            return
        time = int(text)
        if time < self.minimal_delay:
            id = self.bot.send_message("Delay is too small").id
            self.save_message(id)
            self.set_time(chat_id)
            return
        if time > self.maximal_delay:
            time = 1000000000
        self.data_base.REPLACE(
            self.time_table, self.time_cols, (chat_id, time))
        self.bot.send_message(chat_id, "Delay set to {0}".format(time))
        self.start_message(chat_id)

    def get_time(self, chat_id):
        return self.data_base.get_SELECT(
            Database.
            SELECT(("time", )).
            FROM(self.time_table).
            WHERE("chat_id = {0}"
                  .format(chat_id)))[0][0]

    def run(self):
        self.bot.infinity_polling()


Bot(sys.argv[1]).run()