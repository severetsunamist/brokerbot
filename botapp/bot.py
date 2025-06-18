import os
import telebot
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
from .models import Premise
from django.contrib.auth.models import User

# Initialize bot
BOT_TOKEN = ''
bot = telebot.TeleBot(BOT_TOKEN)

# User states
USER_STATES = {}

class UserState:
    def __init__(self):
        self.current_step = None
        self.data = {}
    
    def reset(self):
        self.current_step = None
        self.data = {}

from django.contrib.auth import get_user_model
User = get_user_model()

def get_or_create_user(telegram_user):
    """Get or create Django user from Telegram user"""
    username = f"tg_{telegram_user.id}"
    
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        # Handle cases where Telegram user doesn't have first/last names
        first_name = telegram_user.first_name or "Telegram"
        last_name = telegram_user.last_name or "User"
        
        return User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=None  # No password for Telegram users
        )

# Step handlers
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Добро пожаловать, я - Брокербот, используй /newobject чтобы добавить новый объект.")

# Новый объект - Название
@bot.message_handler(commands=['newobject'])
def start_new_object(message):
    chat_id = message.chat.id
    USER_STATES[chat_id] = UserState()
    USER_STATES[chat_id].current_step = 'name'
    bot.send_message(chat_id, "Давай создадим новый объект.\nКак назовём?")

# Обработка Название и запрос Шоссе
@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'name')
def process_name(message):
    chat_id = message.chat.id
    USER_STATES[chat_id].data['name'] = message.text
    USER_STATES[chat_id].current_step = 'highway'

    markup = ReplyKeyboardMarkup(one_time_keyboard=True,
                                 row_width=2,
                                 resize_keyboard=True,)
    markup.add('в черте МКАД',
                'Ленинградское',
                'Дмитровское',
                'Ярославское',
                'Щелковское',
                'Горьковское',
                'Новорязанское',
                'Каширское',
                'Симферопольское',
                'Калужское',
                'Киевское',
                'Минское',
                'Новорижское',
                'Волоколамское',
                'Пятницкое',
                'М-4',
                'М-11')
    bot.send_message(chat_id, "Какое шоссе?", reply_markup=markup)


# Обработка Шоссе и запрос Координат
@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'highway')
def process_highway(message):
    chat_id = message.chat.id
    USER_STATES[chat_id].data['highway'] = message.text
    USER_STATES[chat_id].current_step = 'location_coords'
    bot.send_message(chat_id, "Пришли координаты через Telegram", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True))

# Тип предложения Аренда/Продажа
@bot.message_handler(content_types=['location'], 
                    func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'location_coords')
def process_location_coords(message):
    chat_id = message.chat.id
    location = message.location
    USER_STATES[chat_id].data['latitude'] = location.latitude
    USER_STATES[chat_id].data['longitude'] = location.longitude
    USER_STATES[chat_id].current_step = 'offer_type'
    
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Продажа', 'Аренда')
    bot.send_message(chat_id, "Аренда или Продажа?", reply_markup=markup)

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'location_coords')
def process_location_coords(message):
    chat_id = message.chat.id
    if not message.location:
        bot.send_message(chat_id, "Нужны координаты или ссылка📍\nили можно выбрать локацию тут ⤵")
        return
    location = message.location
    USER_STATES[chat_id].data['latitude'] = location.latitude
    USER_STATES[chat_id].data['longitude'] = location.longitude
    USER_STATES[chat_id].current_step = 'offer_type'
    
    # # Создать 2 кнопки Продажа, Аренда
    # markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    # markup.add('Аренда', 'Продажа')
    
    # bot.send_message(chat_id, "Так Аренда или Продажа?", reply_markup=markup)

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'offer_type' 
                    and message.text in ['Аренда', 'Продажа'])
def process_offer_type(message):
    chat_id = message.chat.id
    USER_STATES[chat_id].data['offer_type'] = message.text.lower()
    USER_STATES[chat_id].current_step = 'industrial_area'
    
    # Remove the keyboard after selection
    bot.send_message(chat_id, 
                    "Какая площадь производственно-складской части?",
                    reply_markup=ReplyKeyboardRemove())

def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'industrial_area')
def process_industrial_area(message):
    chat_id = message.chat.id
    if not is_float(message.text):
        bot.send_message(chat_id, "Пожалуйста, введите число (Площадь склада, кв.м)")
        return
    
    USER_STATES[chat_id].data['industrial_area'] = float(message.text)
    USER_STATES[chat_id].current_step = 'mezzanine_area'
    bot.send_message(chat_id, "Какая площадь мезонина?")

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'mezzanine_area')
def process_mezzanine_area(message):
    chat_id = message.chat.id
    if not is_float(message.text):
        bot.send_message(chat_id, "Пожалуйста, введите число (Площадь мезонина, кв.м)")
        return
    
    USER_STATES[chat_id].data['mezzanine_area'] = float(message.text)
    USER_STATES[chat_id].current_step = 'office_area'
    bot.send_message(chat_id, "Какая площадь офисов?")

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'office_area')
def process_office_area(message):
    chat_id = message.chat.id
    if not is_float(message.text):
        bot.send_message(chat_id, "Пожалуйста, введите число (Площадь офиса, кв.м)")
        return
    
    USER_STATES[chat_id].data['office_area'] = float(message.text)
    
    if USER_STATES[chat_id].data['offer_type'] == 'аренда':
        USER_STATES[chat_id].current_step = 'industrial_price'
        bot.send_message(chat_id, "Какая ставка аренды склада? (кв.м/год)")
    else:
        USER_STATES[chat_id].current_step = 'sale_price'
        bot.send_message(chat_id, "Какая цена продажи без НДС?")

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'industrial_price')
def process_industrial_price(message):
    chat_id = message.chat.id
    if not is_float(message.text):
        bot.send_message(chat_id, "Пожалуйста, введите число (Ставка аренды склада, руб./кв.м/год)")
        return
    
    USER_STATES[chat_id].data['industrial_price'] = float(message.text)
    USER_STATES[chat_id].current_step = 'mezzanine_price'
    bot.send_message(chat_id, "Какая ставка аренды мезонина? (кв.м/год)")

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'mezzanine_price')
def process_mezzanine_price(message):
    chat_id = message.chat.id
    if not is_float(message.text):
        bot.send_message(chat_id, "Пожалуйста, введите число (Ставка аренды мезонина, руб./кв.м/год)")
        return
    
    USER_STATES[chat_id].data['mezzanine_price'] = float(message.text)
    USER_STATES[chat_id].current_step = 'office_price'
    bot.send_message(chat_id, "Какая ставка аренды офиса")

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'office_price')
def process_office_price(message):
    chat_id = message.chat.id
    if not is_float(message.text):
        bot.send_message(chat_id, "Пожалуйста, введите число (Ставка аренды офиса, руб./кв.м/год)")
        return
    
    USER_STATES[chat_id].data['office_price'] = float(message.text)
    show_confirmation(chat_id)

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'sale_price')
def process_sale_price(message):
    chat_id = message.chat.id
    if not is_float(message.text):
        bot.send_message(chat_id, "Пожалуйста, введите число (Цена продажи, руб.)")
        return
    
    USER_STATES[chat_id].data['sale_price'] = float(message.text)
    show_confirmation(chat_id)

def show_confirmation(chat_id):
    user_data = USER_STATES[chat_id].data
    offer_type = user_data['offer_type']
    
    text = "📋 Пожалуйста проверь что всё правильно:\n\n"
    text += f"🏢 Название: {user_data['name']}\n"
    text += f"📍 Направление: {user_data['highway']}\n"
    text += f"🌐 Координаты: {user_data['latitude']}, {user_data['longitude']}\n"
    text += f"💰 Тип объявления: {offer_type.capitalize()}\n"
    text += f"🏭 Площадь склад/производства: {user_data['industrial_area']} кв.м\n"
    text += f"🏗 Площадь мезонина: {user_data['mezzanine_area']} кв.м\n"
    text += f"🏢 Площадь офиса: {user_data['office_area']} кв.м\n"
    
    if offer_type == 'аренда':
        text += f"🏭 Ставка аренды склада: {user_data['industrial_price']} руб./кв.м/год\n"
        text += f"🏗 Ставка аренды мезонина: {user_data['mezzanine_price']} руб./кв.м/год\n"
        text += f"🏢 Ставка аренды офиса: {user_data['office_price']} руб./кв.м/год\n"
    else:
        text += f"💰 Цена продажи: {user_data['sale_price']} руб. (без НДС)\n"
    
    text += "\nВсё верно?"
    
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Да', 'Нет')
    
    USER_STATES[chat_id].current_step = 'confirmation'
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'confirmation' 
                    and message.text.lower() == 'да')
def process_confirmation_yes(message):
    chat_id = message.chat.id
    user_data = USER_STATES[chat_id].data
    
    # Get or create Django user
    telegram_user = message.from_user
    user = get_or_create_user(telegram_user)
    
    # Create premise object
    premise = Premise(
        creator=user,
        name=user_data['name'],
        highway=user_data['highway'],
        latitude=user_data['latitude'],
        longitude=user_data['longitude'],
        offer_type=user_data['offer_type'],
        industrial_area=user_data['industrial_area'],
        mezzanine_area=user_data['mezzanine_area'],
        office_area=user_data['office_area'],
    )
    
    if user_data['offer_type'] == 'аренда':
        premise.industrial_price = user_data['industrial_price']
        premise.mezzanine_price = user_data['mezzanine_price']
        premise.office_price = user_data['office_price']
    else:
        premise.sale_price = user_data['sale_price']
    
    premise.save()
    
    bot.send_message(chat_id, "✅ Объект создан и добавлен в базу данных!", reply_markup=ReplyKeyboardRemove())
    USER_STATES[chat_id].reset()

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'confirmation' 
                    and message.text.lower() == 'нет')
def process_confirmation_no(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Создание объекта отменено.", reply_markup=ReplyKeyboardRemove())
    USER_STATES[chat_id].reset()

@bot.message_handler(commands=['cancel'])
def cancel_operation(message):
    chat_id = message.chat.id
    if chat_id in USER_STATES:
        USER_STATES[chat_id].reset()
    bot.send_message(chat_id, "Текущая операция отменена.", reply_markup=ReplyKeyboardRemove())

def start_polling():
    bot.infinity_polling()