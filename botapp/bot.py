import os
import telebot
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from telebot.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
from .models import Premise
from django.contrib.auth.models import User

# Initialize bot
BOT_TOKEN = '8104048404:AAEmGvCvBhmSCoA5E3jn5SJQruSYxCQI7KQ'
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
    bot.reply_to(message, "Welcome to Real Estate Bot! Use /newobject to create a new property listing.")

@bot.message_handler(commands=['newobject'])
def start_new_object(message):
    chat_id = message.chat.id
    USER_STATES[chat_id] = UserState()
    USER_STATES[chat_id].current_step = 'name'
    bot.send_message(chat_id, "Let's create a new real estate object.\nPlease enter the name of the premise:")

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'name')
def process_name(message):
    chat_id = message.chat.id
    USER_STATES[chat_id].data['name'] = message.text
    USER_STATES[chat_id].current_step = 'location_text'
    bot.send_message(chat_id, "Please enter the address or location description:")

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'location_text')
def process_location_text(message):
    chat_id = message.chat.id
    USER_STATES[chat_id].data['location_text'] = message.text
    USER_STATES[chat_id].current_step = 'location_coords'
    bot.send_message(chat_id, "Now please share the precise location using Telegram's location sharing feature:",
                    reply_markup=ReplyKeyboardMarkup(
                        [[{'text': "Share Location", 'request_location': True}]],
                        one_time_keyboard=True
                    ))

@bot.message_handler(content_types=['location'], 
                    func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'location_coords')
def process_location_coords(message):
    chat_id = message.chat.id
    location = message.location
    USER_STATES[chat_id].data['latitude'] = location.latitude
    USER_STATES[chat_id].data['longitude'] = location.longitude
    USER_STATES[chat_id].current_step = 'offer_type'
    
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Sale', 'Lease')
    bot.send_message(chat_id, "What type of offer is this?", reply_markup=markup)

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'offer_type' 
                    and message.text.lower() in ['sale', 'lease'])
def process_offer_type(message):
    chat_id = message.chat.id
    USER_STATES[chat_id].data['offer_type'] = message.text.lower()
    USER_STATES[chat_id].current_step = 'industrial_area'
    bot.send_message(chat_id, "Enter available industrial area in sqm:", reply_markup=ReplyKeyboardRemove())

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
        bot.send_message(chat_id, "Please enter a valid number for industrial area:")
        return
    
    USER_STATES[chat_id].data['industrial_area'] = float(message.text)
    USER_STATES[chat_id].current_step = 'mezzanine_area'
    bot.send_message(chat_id, "Enter available mezzanine area in sqm:")

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'mezzanine_area')
def process_mezzanine_area(message):
    chat_id = message.chat.id
    if not is_float(message.text):
        bot.send_message(chat_id, "Please enter a valid number for mezzanine area:")
        return
    
    USER_STATES[chat_id].data['mezzanine_area'] = float(message.text)
    USER_STATES[chat_id].current_step = 'office_area'
    bot.send_message(chat_id, "Enter available office area in sqm:")

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'office_area')
def process_office_area(message):
    chat_id = message.chat.id
    if not is_float(message.text):
        bot.send_message(chat_id, "Please enter a valid number for office area:")
        return
    
    USER_STATES[chat_id].data['office_area'] = float(message.text)
    
    if USER_STATES[chat_id].data['offer_type'] == 'lease':
        USER_STATES[chat_id].current_step = 'industrial_price'
        bot.send_message(chat_id, "Enter price for industrial area (per sqm/month):")
    else:
        USER_STATES[chat_id].current_step = 'sale_price'
        bot.send_message(chat_id, "Enter total sale price (excluding VAT):")

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'industrial_price')
def process_industrial_price(message):
    chat_id = message.chat.id
    if not is_float(message.text):
        bot.send_message(chat_id, "Please enter a valid number for industrial price:")
        return
    
    USER_STATES[chat_id].data['industrial_price'] = float(message.text)
    USER_STATES[chat_id].current_step = 'mezzanine_price'
    bot.send_message(chat_id, "Enter price for mezzanine area (per sqm/month):")

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'mezzanine_price')
def process_mezzanine_price(message):
    chat_id = message.chat.id
    if not is_float(message.text):
        bot.send_message(chat_id, "Please enter a valid number for mezzanine price:")
        return
    
    USER_STATES[chat_id].data['mezzanine_price'] = float(message.text)
    USER_STATES[chat_id].current_step = 'office_price'
    bot.send_message(chat_id, "Enter price for office area (per sqm/month):")

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'office_price')
def process_office_price(message):
    chat_id = message.chat.id
    if not is_float(message.text):
        bot.send_message(chat_id, "Please enter a valid number for office price:")
        return
    
    USER_STATES[chat_id].data['office_price'] = float(message.text)
    show_confirmation(chat_id)

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'sale_price')
def process_sale_price(message):
    chat_id = message.chat.id
    if not is_float(message.text):
        bot.send_message(chat_id, "Please enter a valid number for sale price:")
        return
    
    USER_STATES[chat_id].data['sale_price'] = float(message.text)
    show_confirmation(chat_id)

def show_confirmation(chat_id):
    user_data = USER_STATES[chat_id].data
    offer_type = user_data['offer_type']
    
    text = "📋 Please review the information:\n\n"
    text += f"🏢 Name: {user_data['name']}\n"
    text += f"📍 Location: {user_data['location_text']}\n"
    text += f"🌐 Coordinates: {user_data['latitude']}, {user_data['longitude']}\n"
    text += f"💰 Offer Type: {offer_type.capitalize()}\n"
    text += f"🏭 Industrial Area: {user_data['industrial_area']} sqm\n"
    text += f"🏗 Mezzanine Area: {user_data['mezzanine_area']} sqm\n"
    text += f"🏢 Office Area: {user_data['office_area']} sqm\n"
    
    if offer_type == 'lease':
        text += f"🏭 Industrial Price: {user_data['industrial_price']} per sqm/month\n"
        text += f"🏗 Mezzanine Price: {user_data['mezzanine_price']} per sqm/month\n"
        text += f"🏢 Office Price: {user_data['office_price']} per sqm/month\n"
    else:
        text += f"💰 Sale Price: {user_data['sale_price']} (excluding VAT)\n"
    
    text += "\nIs this information correct?"
    
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Yes', 'No')
    
    USER_STATES[chat_id].current_step = 'confirmation'
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'confirmation' 
                    and message.text.lower() == 'yes')
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
        location_text=user_data['location_text'],
        latitude=user_data['latitude'],
        longitude=user_data['longitude'],
        offer_type=user_data['offer_type'],
        industrial_area=user_data['industrial_area'],
        mezzanine_area=user_data['mezzanine_area'],
        office_area=user_data['office_area'],
    )
    
    if user_data['offer_type'] == 'lease':
        premise.industrial_price = user_data['industrial_price']
        premise.mezzanine_price = user_data['mezzanine_price']
        premise.office_price = user_data['office_price']
    else:
        premise.sale_price = user_data['sale_price']
    
    premise.save()
    
    bot.send_message(chat_id, "✅ Object successfully saved to database!", reply_markup=ReplyKeyboardRemove())
    USER_STATES[chat_id].reset()

@bot.message_handler(func=lambda message: USER_STATES.get(message.chat.id, UserState()).current_step == 'confirmation' 
                    and message.text.lower() == 'no')
def process_confirmation_no(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Object creation cancelled.", reply_markup=ReplyKeyboardRemove())
    USER_STATES[chat_id].reset()

@bot.message_handler(commands=['cancel'])
def cancel_operation(message):
    chat_id = message.chat.id
    if chat_id in USER_STATES:
        USER_STATES[chat_id].reset()
    bot.send_message(chat_id, "Current operation cancelled.", reply_markup=ReplyKeyboardRemove())

def start_polling():
    bot.infinity_polling()