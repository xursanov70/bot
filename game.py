import telebot
from telebot import types
import random
import mysql.connector 
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


# Database connection setup
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="123",
    database="game-bot"
)
cursor = db.cursor()

TOKEN = '7326826275:AAF0tEpai10p1EWQbKfmfokbtjuVKUkQSJ4'
bot = telebot.TeleBot(TOKEN, parse_mode=None)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    username = message.from_user.username
    chat_id = message.from_user.id

    # Check if user is already in the database
    cursor.execute("SELECT * FROM users WHERE chat_id = %s", (chat_id,))
    user_exists = cursor.fetchone()

    if user_exists:
        # If the user exists, show the game options directly
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        game_button = types.KeyboardButton("start game")
        result_button = types.KeyboardButton("results")
        markup.add(game_button, result_button)

        reply = f"Assalamu alaykum, {username}.\nBotimizga xush kelibsiz!"
        bot.send_message(message.chat.id, reply, reply_markup=markup)
    else:
        # If the user does not exist, ask for contact information
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        phone_button = types.KeyboardButton("Send phone number", request_contact=True)
        markup.add(phone_button)

        reply = f"Assalamu alaykum, {username}.\nBotimizga xush kelibsiz!"
        reply1 = "Iltimos, telefon raqamingizni kiriting!"

        bot.send_message(message.chat.id, reply, reply_markup=markup)
        bot.send_message(message.chat.id, reply1, reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    if message.contact is not None:
        phone_number = message.contact.phone_number
        chat_id = message.from_user.id
        username = message.from_user.username

        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE chat_id = %s", (chat_id,))
        user_exists = cursor.fetchone()

        if not user_exists:
            # Insert user info into the database
            cursor.execute("INSERT INTO users (chat_id, username, phone_number) VALUES (%s, %s, %s)", 
                           (chat_id, username, phone_number))
            db.commit()
            bot.send_message(message.chat.id, "Rahmat! Telefon raqamingiz qabul qilindi.")
        
        # Ask for the user's name without showing the phone button
        bot.send_message(message.chat.id, "Iltimos, ismingizni kiriting:")
        bot.register_next_step_handler(message, name_input_handler)
        

def name_input_handler(message):
    name = message.text
    chat_id = message.from_user.id
    if name:
        cursor.execute("UPDATE users SET name = %s WHERE chat_id = %s", (name, chat_id))
        db.commit()

        bot.send_message(message.chat.id, f"Rahmat, {name}! Ismingiz qabul qilindi.")

        # Display the options for the game after the name is accepted
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        game_button = types.KeyboardButton("start game")
        result_button = types.KeyboardButton("results")
        markup.add(game_button, result_button)
        bot.send_message(message.chat.id, "Siz qaysi birini xohlaysiz?", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Iltimos, ismingizni kiriting:")

@bot.message_handler(func=lambda message: message.text == "start game")
def start_game(message):
    chat_id = message.from_user.id
    
    # Increment game_count when starting the game
    cursor.execute("UPDATE users SET game_count = game_count + 1 WHERE chat_id = %s", (chat_id,))
    db.commit()

    rand_number = random.randint(1, 10)
    bot.send_message(message.chat.id, "Men 1 dan 10 gacha son o'yladim. Iltimos, son kiriting:")
    
    bot.register_next_step_handler(message, guess_number, rand_number, 0)

def guess_number(message, rand_number, guesses):
    try:
        user_guess = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Iltimos, to'g'ri raqam kiriting!")
        bot.register_next_step_handler(message, guess_number, rand_number, guesses)
        return

    guesses += 1

    if user_guess < rand_number:
        bot.send_message(message.chat.id, "Men o'ylagan son bundan kattaroq. Yana harakat qiling.")
        bot.register_next_step_handler(message, guess_number, rand_number, guesses)
    elif user_guess > rand_number:
        bot.send_message(message.chat.id, "Men o'ylagan son bundan kichikroq. Yana harakat qiling.")
        bot.register_next_step_handler(message, guess_number, rand_number, guesses)
    else:
        bot.send_message(message.chat.id, f"Tabriklayman! Siz {guesses} ta urinishda topdingiz!")

        # Update the attempts count in the database
        chat_id = message.from_user.id
        cursor.execute("UPDATE users SET attempt = attempt + %s WHERE chat_id = %s", (guesses, chat_id))
        db.commit()

        # Show the game and results options again after completing the game
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        game_button = types.KeyboardButton("start game")
        result_button = types.KeyboardButton("results")
        markup.add(game_button, result_button)
        # bot.send_message(message.chat.id, "Yana o'yin o'ynaysizmi yoki natijalarni ko'rishni xohlaysizmi?", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "results")
def show_results(message):
    chat_id = message.from_user.id
    
    # Fetch name and attempts (or results) from the database
    cursor.execute("SELECT name, attempt, game_count FROM users ORDER BY attempt DESC")
    results = cursor.fetchall()

    if results:
        result_message = "Natijalar:\n"
        for idx, (name, attempt, game_count) in enumerate(results, start=1):
            result_message += f"{idx}. {name} - {game_count} o'yin(lar) - {attempt} urinish(lar)\n"
    else:
        result_message = "Natijalar hozircha mavjud emas."
    
    bot.send_message(message.chat.id, result_message)

    # Show the game and results options again after showing results
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    game_button = types.KeyboardButton("start game")
    result_button = types.KeyboardButton("results")
    markup.add(game_button, result_button)
    # bot.send_message(message.chat.id, "Yana o'yin o'ynaysizmi yoki natijalarni ko'rishni xohlaysizmi?", reply_markup=markup)


bot.infinity_polling()
