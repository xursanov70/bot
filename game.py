import telebot
import time
import random

TOKEN = '7326826275:AAF0tEpai10p1EWQbKfmfokbtjuVKUkQSJ4'

bot =  telebot.TeleBot(TOKEN, parse_mode=None)



@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    username = message.from_user.username
    reply = f"test, {username}\n" 
    reply1 = f"Botimizga xush kelibsiz!"

    bot.reply_to(message, reply)
    time.sleep(1) 

    bot.reply_to(message, reply1)
    time.sleep(1) 



# @bot.message_handler(func=lambda m: True)
# def messages(message):
#     guesses = 0
#     rand = random.randint(1, 10)
    
#     bot.reply_to(message, f"1 dan 10 gacha son kiriting:")
#     test = True

#     while test:
#         try:
#             number = int(message.text)
#         except ValueError:
#             bot.reply_to(message, "Iltimos, raqam kiriting.")
#             break

#         guesses += 1

#         if rand > number:
#             bot.reply_to(message, f"Men o'ylagan son bundan kattaroq. Yana harakat qilib ko'ring")
#         elif rand < number:
#             bot.reply_to(message, f"Men o'ylagan son bundan kichikroq. Yana harakat qilib ko'ring")
#         else:
#             bot.reply_to(message, f"Tabriklaymiz, {guesses} ta taxmin bilan topdingiz!")
#             break
            


bot.infinity_polling()