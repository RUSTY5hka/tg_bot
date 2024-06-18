import asyncio
import schedule
from telethon.sync import TelegramClient
from telethon.tl.types import ChannelParticipantsSearch
from telethon.tl.functions.channels import GetParticipantsRequest
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
import json
import time
from threading import Thread


# Конфигурация Telethon
api_id = '14489844'
api_hash = '5a3e00673bb226cf4fd2b5cd34847660'
bot_token = '7436664517:AAGh8J6LoHOp2aSmlICU9eRvimIF6e_MVS4'
group_username = -1001876784219

bot = TeleBot(bot_token)

# Инициализация Telethon клиента
client = TelegramClient('session_name', api_id, api_hash)

def create_keyboard(buttons_list):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard


async def get_participants():
    await client.start(bot_token=bot_token)
    group = await client.get_entity(group_username)

    all_participants = []
    offset = 0
    limit = 100

    while True:
        participants = await client(GetParticipantsRequest(
            group, ChannelParticipantsSearch(''), offset, limit, hash=0
        ))

        if not participants.users:
            break

        all_participants.extend(participants.users)
        offset += len(participants.users)

    name_list = [user.first_name for user in all_participants]
    last_name_list = [user.last_name for user in all_participants]
    user_id_list = [user.id for user in all_participants]

    await client.disconnect()
    return name_list, last_name_list, user_id_list

@bot.message_handler(commands=['start'])
def start(message):
    user_id=message.chat.id
    bot.send_message(user_id, 'Привет, я бот, который отправляет список пользователей покинувших ваш телеграм канал', reply_markup=create_keyboard(['Получить список пользователей которые покинули ваш телеграм канал']))
    with open('send_to.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    if user_id not in data['user_id']:
        data['user_id'].append(message.chat.id)
    with open('send_to.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

@bot.message_handler(func=lambda message: message.text.lower() == "получить список пользователей которые покинули ваш телеграм канал")
def get_list_exited_users(message):
    bot.send_message(message.chat.id, 'Бот думает...')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    name_list, last_name_list, user_id_list = loop.run_until_complete(get_participants())
    message_with_exited_users='Вот список пользователей которые покинули ваш телеграм канал:\n'
    with open('previous_users.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    previous_users_id = data["user_id"]
    current_users_id = user_id_list
    users_id_left = list(set(previous_users_id) - set(current_users_id))
    for user_id in users_id_left:
        try:
            index = data["user_id"].index(user_id)
            name = data["name"][index]
            last_name = data["last_name"][index]
            message_with_exited_users += f'user_id:{user_id}, Имя:{name}, Фамилия:{last_name}\n'
        except:
            continue

    bot.send_message(message.chat.id, message_with_exited_users, reply_markup=create_keyboard(['Получить список пользователей которые покинули ваш телеграм канал']))

    new_users=list(set(current_users_id) - set(previous_users_id))

    if new_users is not None:
        with open('previous_users.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        for user in new_users:
            index = current_users_id.index(user)
            data["user_id"].append(user)
            data["name"].append(name_list[index])
            data["last_name"].append(last_name_list[index])
            with open('previous_users.json', 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)



def send_report():
    with open('send_to.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    for user_id in data['user_id']:
            bot.send_message(user_id, 'Бот думает...')
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            name_list, last_name_list, user_id_list = loop.run_until_complete(get_participants())
            message_with_exited_users = 'Вот список пользователей которые покинули ваш телеграм канал:\n'
            with open('previous_users.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
            previous_users_id = data["user_id"]
            current_users_id = user_id_list
            users_id_left = list(set(previous_users_id) - set(current_users_id))
            for user_id in users_id_left:
                try:
                    index = data["user_id"].index(user_id)
                    name = data["name"][index]
                    last_name = data["last_name"][index]
                    message_with_exited_users += f'user_id:{user_id}, Имя:{name}, Фамилия:{last_name}\n'
                except:
                    continue

            bot.send_message(user_id, message_with_exited_users, reply_markup=create_keyboard(
                ['Получить список пользователей которые покинули ваш телеграм канал']))

            new_users = list(set(current_users_id) - set(previous_users_id))

            if new_users is not None:
                with open('previous_users.json', 'r', encoding='utf-8') as file:
                    data = json.load(file)
                for user in new_users:
                    index = current_users_id.index(user)
                    data["user_id"].append(user)
                    data["name"].append(name_list[index])
                    data["last_name"].append(last_name_list[index])
                    with open('previous_users.json', 'w', encoding='utf-8') as file:
                        json.dump(data, file, ensure_ascii=False, indent=4)
def schedule_runner():
    while True:
        schedule.run_pending()
        time.sleep(1)
schedule.every().day.at("23:55").do(send_report)
Thread(target = schedule_runner).start()

bot.infinity_polling()