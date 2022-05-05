import os
import requests
import time
import logging
import telegram

from dotenv import load_dotenv
from telegram.ext import Updater

from exceptions import *

load_dotenv()

logging.basicConfig(
    filename='main.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s - %(lineno)d',
    level=logging.INFO)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """отправляем сообщение"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f"Сообщение успешно отправлено '{message}'")
    except Exception as error:
        logging.error(f"Сообщение не было отправлено, ошибка: {error}")


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса. Возвращает ответ API"""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        api_answer = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except Exception as error:
        raise EndpointNotWorking(error)

    if api_answer.status_code != 200:
        raise StatusCodeIsNot200(
            api_answer.url, api_answer.status_code
        )
    return api_answer.json()


def check_response(response):
    """проверяет ответ API и возвращает результат"""
    hw = response['homeworks']

    if not isinstance(hw, list):
        raise OtherDataType(type(hw))

    if hw is None:
        raise NotKeyHomeworks()
    return hw[0]


def parse_status(homework):
    """
    функция возвращает подготовленную для отправки в Telegram строку,
    содержащую один из вердиктов словаря HOMEWORK_STATUSES
    """
    if "homework_name" not in homework or "status" not in homework:
        raise NoKeysInAPI()

    homework_name = homework["homework_name"]
    homework_status = homework["status"]

    if homework_status not in HOMEWORK_STATUSES.keys():
        raise UndocumentedStatus(homework_status)

    verdict = HOMEWORK_STATUSES.get(homework_status)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяем токены и айди чата"""
    lst_token_id = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    lst_token_name = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN',
                      'TELEGRAM_CHAT_ID']

    for name in lst_token_id:
        if name is None:
            logging.critical(
                f"Отсутствует обязательная переменная окружения: "
                f"{lst_token_name[lst_token_id.index(name)]}"
            )
            return False
    return True


def main():
    """Основная логика работы бота."""
    check_message_error = ''
    check_message_text = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    if check_tokens():
        while True:
            try:
                response = get_api_answer(1111111)
                homework = check_response(response)
                text_message = parse_status(homework)
                if check_message_text != text_message:
                    send_message(bot, text_message)
                    check_message_text = text_message
                else:
                    logging.debug('Отсутствие в ответе новых статусов')
                time.sleep(RETRY_TIME)

            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                logging.error(message)
                if check_message_error != message:
                    send_message(bot, message)
                    check_message_error = message
                time.sleep(RETRY_TIME)
    else:
        raise NotValueInTokenIdError()



if __name__ == '__main__':
    main()
