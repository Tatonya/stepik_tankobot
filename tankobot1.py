import telebot
import requests
import json
import os
import redis

token = os.environ['BOT_TOKEN']
bot = telebot.TeleBot(token)
api_url = 'https://stepik.akentev.com/api/stress'
MAIN_STATE = 'main'
ASKING_QUESTION = 'asking_question'
LETTERS = ("ц", "у", "к", "е", "н", "г", "ш", "щ", "з", "а"
           , "х", "ф", "в", "п", "р", "о", "л", "д", "ж", "э", "ч", "с", "м", "и", "т", "б")
redis_url = os.environ.get('REDIS_URL')
if redis_url is None:

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
else:
    redis_db = redis.from_url(redis_url,decode_responses=True)
    raw_data = redis_db.get('data')
    if raw_data is None:
        data = {
            "states": {},
            "question": {},
            "first_letter": {},
            "vic": {},
            "def": {}
        }
    else:
        data = json.load(raw_data)


def change_data(key, user_id, value):
    data[key][user_id] = value
    if redis_url is None:
        json.dump(data, open('tankobot_data.json', 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    else:
        redis_db = redis.from_url(redis_url,decode_responses=True)
        redis_db.set('data', json.dumps(data))


def choose_and_send_question(func_letter, func_user_id):
    '''меняет состояние бота на ASKING_QUESTION, выбирает слово и отправляет вопрос пользователю'''
    change_data('states', func_user_id, ASKING_QUESTION)
    change_data('question', func_user_id, requests.get(
        api_url, params={'first_letter': func_letter}
    ).json()['word'])
    ask = 'На какую букву нужно поставить ударение в слове "{}" ?'.format(data['question'][func_user_id].lower())
    bot.send_message(func_user_id, ask)


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
                             "Сбросить счёт и выбор буквы - отправьте \"Заново\"\n"
                             "                         "))
    elif message.text.lower() == 'привет':
        bot.send_message(user_id, "Ну привет!")
    elif 'только на букву ' in message.text.lower() and message.text.lower()[-1] in LETTERS:
        letter = message.text.lower()[-1]
        bot.send_message(user_id, 'Хорошо, спрашиваю слова на букву {}.'.format(letter))
        change_data('first_letter', user_id, letter)
        choose_and_send_question(letter, user_id)
    elif message.text.lower() == 'на любую букву':
        bot.send_message(user_id, 'Хорошо, спрашиваю слова на любую букву')
        letter = None
        change_data('first_letter', user_id, letter)
        choose_and_send_question(letter, user_id)
    elif message.text.lower() == 'спроси меня слово':
        letter = data['first_letter'].get(user_id)
        choose_and_send_question(letter, user_id)


    elif message.text.lower() == 'покажи счет':
        bot.send_message(user_id,
                         "Верно {}\tОшибок {}".format(data['vic'][user_id], data['def'][user_id]))
        change_data('states', user_id, MAIN_STATE)
    elif message.text.lower() == 'заново':
        bot.send_message(user_id,
                         "Хорошо, начнём сначала. ")
        change_data('vic', user_id, 0)
        change_data('def', user_id, 0)
        change_data('first_letter', user_id, None)
        change_data('states', user_id, MAIN_STATE)

    else:
        bot.send_message(user_id, 'Я тебя не понял.')
        change_data('states', user_id, MAIN_STATE)


def asking_question(message):
    '''Сравнивает ответ пользователя с вопросом, хвалит/ругает, начисляет очки'''
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
