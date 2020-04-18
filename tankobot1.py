'''Done! Congratulations on your new bot. You will find it at t.me/TankoStepikBot. You can now add a description, about section and profile picture for your bot, see /help for a list of commands. By the way, when you've finished creating your cool bot, ping our Bot Support if you want a better username for it. Just make sure the bot is fully operational before you do this.

Use this token to access the HTTP API:
1125523623:AAFqJKIVDwJVGqy6d-TDNxBSkaliXJjiawU
Keep your token secure and store it safely, it can be used by anyone to control your bot.

For a description of the Bot API, see this page: https://core.telegram.org/bots/api'''
import telebot
import requests
import json

token = '1125523623:AAFqJKIVDwJVGqy6d-TDNxBSkaliXJjiawU'
bot = telebot.TeleBot(token)
api_url = 'https://stepik.akentev.com/api/stress'
MAIN_STATE = 'main'
ASKING_QUESTION = 'asking_question'
LETTERS = ("ц", "у", "к", "е", "н", "г", "ш", "щ", "з", "а"
           , "х", "ф", "в", "п", "р", "о", "л", "д", "ж", "э", "ч", "с", "м", "и", "т", "б")
try:
    data = json.load(open('tankobot_data.json', 'r', encoding='utf-8'))
except FileNotFoundError:
    data = {
        "states": {},
        "question": {},
        "first_letter": {},
        "vic": {},
        "def": {}
    }


def change_data(key, user_id, value):
    data[key][user_id] = value
    json.dump(data, open('tankobot_data.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)


@bot.message_handler(func=lambda message: True)
def dispatcher(message):
    user_id = str(message.from_user.id)
    state = data['states'].get(user_id, MAIN_STATE)
    if user_id not in data['vic']:
        change_data('vic', user_id, 0)
    if user_id not in data['def']:
        change_data('def', user_id, 0)
    if state == MAIN_STATE:
        main_handler(message)
    elif state == ASKING_QUESTION:
        asking_question(message)


def main_handler(message):
    user_id = str(message.from_user.id)
    if message.text == '/start':
        bot.send_message(user_id,
                         (
                             "Это  бот-тренажер ударений: он поможет научиться правильной постановке ударений в сложных словах. \n"
                             "                         Тренироваться - отправьте \"Спроси меня слово\"\n"
                             "                         Тренировать слова на выбранную букву - отправьте \"Только на букву ..\"\n"
                             "                         Отменить выбор буквы - отправьте \"На любую букву\"\n"
                             "                         Посмотреть счет - отправьте \"Покажи счет\"\n"
                             "                         \n"
                             "                         "))
    elif message.text.lower() == 'привет':
        bot.send_message(user_id, "Ну привет!")
    elif 'только на букву ' in message.text.lower() and message.text.lower()[-1] in LETTERS:
        letter = message.text.lower()[-1]
        bot.send_message(user_id, 'Хорошо, спрашиваю слова на букву {}.'.format(letter))
        change_data('first_letter', user_id, letter)
        change_data('states', user_id, ASKING_QUESTION)
        change_data('question', user_id, requests.get(
            api_url, params={'first_letter': letter}
        ).json()['word'])
        ask = 'На какую букву нужно поставить ударение в слове "{}" ?'.format(data['question'][user_id].lower())
        bot.send_message(user_id, ask)
    elif message.text.lower() == 'на любую букву':
        bot.send_message(user_id, 'Хорошо, спрашиваю слова на любую букву')
        change_data('first_letter', user_id, None)
        change_data('states', user_id, ASKING_QUESTION)
        letter = data['first_letter'].get(user_id)
        change_data('question', user_id, requests.get(
            api_url, params={'first_letter': letter}
        ).json()['word'])
        ask = 'На какую букву нужно поставить ударение в слове "{}" ?'.format(data['question'][user_id].lower())
        bot.send_message(user_id, ask)
    elif message.text.lower() == 'спроси меня слово':
        letter = data['first_letter'].get(user_id)
        change_data('question', user_id, requests.get(
            api_url, params={'first_letter': letter}
        ).json()['word'])
        ask = 'На какую букву нужно поставить ударение в слове "{}" ?'.format(data['question'][user_id].lower())
        bot.send_message(user_id, ask)
        change_data('states', user_id, ASKING_QUESTION)

    elif message.text.lower() == 'покажи счет':
        bot.send_message(user_id,
                         "Верно {}\tОшибок {}".format(data['vic'][user_id], data['def'][user_id]))
        change_data('states', user_id, MAIN_STATE)

    else:
        bot.send_message(user_id, 'Я тебя не понял.')
        change_data('states', user_id, MAIN_STATE)


def asking_question(message):
    user_id = str(message.from_user.id)
    if message.text == data['question'][user_id]:
        bot.send_message(user_id, "Правильно!")
        new_vic = data['vic'][user_id] + 1
        change_data('vic', user_id, new_vic)
        change_data('states', user_id, MAIN_STATE)

    else:
        bot.send_message(user_id, "Неправильно :(")
        new_def = data['def'][user_id] + 1
        change_data('def', user_id, new_def)
        change_data('states', user_id, MAIN_STATE)


bot.polling()

print('Бот остановлен. Можно сохранить данные на диск')
