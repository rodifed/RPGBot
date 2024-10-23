import telebot
import string
import math
import os
import text
from db import users, heals, locations
from telebot.types import InlineKeyboardButton as IB
from telebot.types import Message
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("token")

bot = telebot.TeleBot(token)

temp = {}

clear = telebot.types.ReplyKeyboardRemove()

def register_1(msg: Message):
    bot.send_message(msg.chat.id, text=text.hi_message%msg.from_user.first_name)
    bot.register_next_step_handler(msg, register_2)

def register_2(msg: Message):
    if not temp[msg.chat.id]['name']:
        temp[msg.chat.id]['name'] = msg.text
    kb = telebot.types.ReplyKeyboardMarkup(True, True)
    kb.row('Земля 🌍', 'Вода 💦')
    kb.row('Огонь 🔥', 'Воздух 🌬️')
    bot.send_message(msg.chat.id, "Выбери свою стихию, падаван. Земля 🌍, Вода 💦, Огонь 🔥, Воздух 🌬️", reply_markup=kb)
    bot.register_next_step_handler(msg, register_3)

def register_3(msg: Message):
    if msg.text == "Огонь 🔥":
        bot.send_message(msg.chat.id, "Магия Огня 🔥 под запретом")
        register_2(msg)
        return
    elif msg.text in ["Земля 🌍", "Вода 💦", "Огонь 🔥", "Воздух 🌬️"]:
        temp[msg.chat.id]["power"] = msg.text
        users.write([msg.chat.id,
                    temp[msg.chat.id]["name"],
                    temp[msg.chat.id]["power"],
                    0,0,10,0
                    ])
        heals.write([
            msg.chat.id,
            {}
        ])
        bot.send_message(msg.chat.id, text.thanks, reply_markup=clear)
    else:
        bot.send_message(msg.chat.id, "Стихии %s не существует."%msg.text)
        register_2(msg)
        


def is_new(msg: Message):
    result = users.read_all()
    for user in result:
        if user[0] == msg.chat.id:
            return False
        
    return True

@bot.message_handler(commands=['start'])
def start(msg: Message):
    if is_new(msg):
        register_1(msg)
        temp[msg.chat.id] = {'name': None}
    else:
        menu(msg)

@bot.message_handler(commands=['menu'])
def menu(msg: Message):
    bot.send_message(msg.chat.id, text.menu_text, reply_markup=clear)

@bot.message_handler(commands=["square"])
def square(msg: Message):
    kb = telebot.types.ReplyKeyboardMarkup(True, True)
    kb.row("Тренироваться")
    kb.row("Тест на силу")
    bot.send_message(msg.chat.id, text.training, reply_markup=kb)
    bot.register_next_step_handler(msg, square_handler)
    bot.send_message(msg.chat.id, text.broom_error)
    bot.send_message(msg.chat.id, text.menu_text)


def square_handler(msg: Message):
    if msg.text == "Тренироваться":
        pass
    elif msg.text == "Тест на силу":
        pass
    else:
        error_tpa(msg)

 

@bot.message_handler(commands=["home"])
def home(msg: Message):
    kb = telebot.types.ReplyKeyboardMarkup()
    kb.row("Отдохнуть")
    kb.row("Перекусить")
    bot.send_message(msg.chat.id, text.city, reply_markup=kb)
    bot.register_next_step_handler(msg, home_handler)


def home_handler(msg):
    if msg.text == 'Отдохнуть':
        pass
    elif msg.text == 'Перекусить':
        kb = inline_heal(msg)
        bot.send_message(msg.chat.id, "Что будешь есть?", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def home_callback_query(call):
    print(call.data)
    if call.data.startswith("food_"):
        food_data = call.data.split("_")
        eating(call.message, food_data[1], food_data[2])
        heals_data = heals.read("user_id", call.message.chat.id)[1]
        kb = telebot.types.InlineKeyboardMarkup()
        for name in heals_data.keys():
            kb.row(IB(f"{name}, {heals_data[name][0]} HP+, {heals_data[name][1]} шт.",
                  callback_data=f"food_{name}_{heals_data[name][0]}"))
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=kb)
    
        
def eating(msg, key, hp):
    _, data = heals.read("user_id", msg.chat.id)
    user = users.read("user_id", msg.chat.id)
    if data[key][1] == 1:
        del data[key]
    else:
        data[key][1] -= 1
    heals.write([msg.chat.id, data])
    user[3] += int(hp)
    users.write(user)
    print("Игрок поел")
    
    

@bot.message_handler(commands=["addheal"])
def add_heal(msg: Message):
    _, heals_data = heals.read("user_id", msg.chat.id)
    heals_data["Soup"] = [10, 1]
    heals_data["Meat"] = [20, 2]
    heals_data["Maccaroni"] = [5, 3]
    heals_data["Sousages"] = [10, 5]
    heals_data["Bread"] = [1, 10]
    heals.write([msg.chat.id, heals_data])
    bot.send_message(msg.chat.id, "Еда была выдана.")


def inline_heal(msg: Message):
    heals_data = heals.read("user_id", msg.chat.id)[1]
    kb = telebot.types.InlineKeyboardMarkup()
    for name in heals_data.keys():
        kb.row(IB(f"{name}, {heals_data[name][0]} HP+, {heals_data[name][1]} шт.",
                  callback_data=f"food_{name}_{heals_data[name][0]}"))
    return kb



def broom_query_1(msg: Message):
    if msg.text == 'Воспользоваться метлой':
        broom(msg.chat.id)
        bot.register_next_step_handler(msg, broom_query_2)

def broom_query_2(msg: Message):
    global broom_ready
    if msg.text == "Домой":
        bot.send_message(msg.chat.id, "Команда: /home", reply_markup=clear)
        broom_ready = True
    elif msg.text == "Площадь тренировок":
        bot.send_message(msg.chat.id, "Команда: /square", reply_markup=clear)
        broom_ready = True

def broom(chat_id: int):
    bot.send_message(chat_id, "Метла", reply_markup=clear)
    kb = telebot.types.ReplyKeyboardMarkup(True, True)
    kb.row("Домой")
    kb.row("Площадь тренировок")
    bot.send_message(chat_id, "Локации", reply_markup=kb)

def error_tpa(msg: Message):
    kb = telebot.types.ReplyKeyboardMarkup(True, True)
    kb.row("Воспользоваться метлой")
    bot.send_message(msg.chat.id, text.sorry, reply_markup=kb)
    bot.register_next_step_handler(msg, broom_query_1)


@bot.message_handler(commands=["broom"])
def broom_tpa(msg: Message):
    kb = telebot.types.ReplyKeyboardMarkup(True, True)
    kb.row("Воспользоваться метлой")
    bot.send_message(msg.chat.id, text.broom, reply_markup=kb)
    bot.register_next_step_handler(msg, broom_query_1)

@bot.message_handler(commands=["tpa"])
def tpa(msg: Message):
    kb = telebot.types.ReplyKeyboardMarkup(True, True)
    kb.row("Статистика", "Уроки")
    kb.row("Телепортация")
    bot.send_message(msg.chat.id, "Дом", reply_markup=kb)
    bot.register_next_step_handler(msg, tpa_2)

def tpa_2(msg: Message):
    if msg.text == "Статистика":
        stats(msg)
    elif msg.text == "Уроки":
        lessons(msg)
    elif msg.text == "Телепортация":
        tpa_out(msg)

def stats(msg: Message):
    def get_user():
        for user in users.read_all():
            if user[0] == msg.chat.id:
                return user
    bot.send_message(msg.chat.id, "Твоя статистика: "+str(get_user()[5])+" баллов, "+str(get_user()[5])+" уровень")

def lessons():
    pass

def tpa_out():
    pass





if __name__ == "__main__":
    bot.infinity_polling()