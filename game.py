import telebot
from telebot import types
import random
import mysql.connector 
import os
from dotenv import load_dotenv

load_dotenv()



db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="123",
    database="game-bot"
)
cursor = db.cursor()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN, parse_mode=None)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    username = message.from_user.username
    chat_id = message.from_user.id

    cursor.execute("SELECT * FROM users WHERE chat_id = %s", (chat_id,))
    user_exists = cursor.fetchone()

    if user_exists:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        game_button = types.KeyboardButton("start game")
        result_button = types.KeyboardButton("results")
        markup.add(game_button, result_button)

        reply = f"Assalamu alaykum, {username}.\nBotimizga xush kelibsiz!"
        bot.send_message(message.chat.id, reply, reply_markup=markup)
    else:
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

        cursor.execute("SELECT * FROM users WHERE chat_id = %s", (chat_id,))
        user_exists = cursor.fetchone()

        if not user_exists:
            cursor.execute("INSERT INTO users (chat_id, username, phone_number) VALUES (%s, %s, %s)", 
                           (chat_id, username, phone_number))
            db.commit()
            bot.send_message(message.chat.id, "Rahmat! Telefon raqamingiz qabul qilindi.")
        
        bot.send_message(message.chat.id, "Iltimos, ismingizni kiriting:")
        bot.register_next_step_handler(message, name_input_handler)
        

def name_input_handler(message):
    name = message.text
    chat_id = message.from_user.id
    if name:
        cursor.execute("UPDATE users SET name = %s WHERE chat_id = %s", (name, chat_id))
        db.commit()

        bot.send_message(message.chat.id, f"Rahmat, {name}! Ismingiz qabul qilindi.")

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        game_button = types.KeyboardButton("start game")
        result_button = types.KeyboardButton("results")
        markup.add(game_button, result_button)
        bot.send_message(message.chat.id, "O'yinni boshlash uchun start game tugmasini bosing", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Iltimos, ismingizni kiriting:")

@bot.message_handler(func=lambda message: message.text == "start game")
def start_game(message):
    chat_id = message.from_user.id
    
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

        chat_id = message.from_user.id
        cursor.execute("UPDATE users SET attempt = attempt + %s WHERE chat_id = %s", (guesses, chat_id))
        db.commit()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        game_button = types.KeyboardButton("start game")
        result_button = types.KeyboardButton("results")
        markup.add(game_button, result_button)


@bot.message_handler(func=lambda message: message.text == "results")
def show_results(message):
    chat_id = message.from_user.id
    
    # Fetch top 10 results
    cursor.execute("SELECT name, attempt, game_count FROM users ORDER BY attempt DESC LIMIT 10")
    top_results = cursor.fetchall()
    
    # Fetch the current user's result (you can customize this query based on how user info is stored)
    cursor.execute("SELECT name, attempt, game_count FROM users WHERE chat_id = %s", (chat_id,))
    my_result = cursor.fetchone()

    result_message = "Natijalar:\n"
    
    # Display the top 10 results
    if top_results:
        for idx, (name, attempt, game_count) in enumerate(top_results, start=1):
            result_message += f"{idx}. ismi: {name}\n o'yin soni: {game_count}\n urinish: {attempt}\n"
    else:
        result_message = "Natijalar hozircha mavjud emas.\n"

    # Add the current user's result with a special label if it exists
    if my_result:
        name, attempt, game_count = my_result
        result_message += f"\n{idx}. ismi: {name}\n o'yinlar soni: {game_count}\n urinishlar soni: {attempt}\n"
    else:
        result_message += "\nSizning natijangiz hali mavjud emas."

    bot.send_message(message.chat.id, result_message)

    # Show the game and results options again after showing results
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    game_button = types.KeyboardButton("start game")
    result_button = types.KeyboardButton("results")
    markup.add(game_button, result_button)


bot.infinity_polling()
