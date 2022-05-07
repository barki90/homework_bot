import os
import requests
import time
import logging
import telegram
import sys

from dotenv import load_dotenv
from http import HTTPStatus

from exceptions import (EmptyAPIResponseError, StatusCodeIsNot200,
                        EndpointNotWorking, UndocumentedStatus)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """отправляем сообщение."""
    try:
        logging.info("Началась отправка сообщения")
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logging.error(f"Сообщение не было отправлено, ошибка: {error}")
    else:
        logging.info(f"Сообщение успешно отправлено '{message}'")


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса. Возвращает ответ API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        api_answer = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except Exception as error:
        raise EndpointNotWorking(error)
    if api_answer.status_code != HTTPStatus.OK:
        raise StatusCodeIsNot200(
            api_answer.url, api_answer.status_code
        )
    return api_answer.json()


def check_response(response):
    """проверяет ответ API и возвращает результат."""
    logging.info("Началась проверка ответа сервера")
    if not isinstance(response, dict):
        raise TypeError
    if "homeworks" not in response or "current_date" not in response:
        raise EmptyAPIResponseError()
    return response["homeworks"][0]


def parse_status(homework):
    """
    Функция возвращает подготовленную для отправки в Telegram строку.
    содержащую один из вердиктов словаря HOMEWORK_STATUSES
    """
    if "homework_name" not in homework:
        raise KeyError("homework_name отсутствует в homework")
    homework_name = homework["homework_name"]
    homework_status = homework["status"]
    if homework_status not in HOMEWORK_STATUSES.keys():
        raise UndocumentedStatus(homework_status)
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяем токены и айди чата."""
    lst_token_id = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    return all(lst_token_id)


def main():
    """Основная логика работы бота."""
    check_message_error = ''
    check_message_text = ''
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - 86400 * 10
    if not check_tokens():
        message = 'Отсутствует обязательная переменная окружения'
        logging.critical(message)
        sys.exit(message)
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            text_message = parse_status(homework)
            if check_message_text != text_message:
                send_message(bot, text_message)
                check_message_text = text_message
            else:
                logging.debug('Отсутствие в ответе новых статусов')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if check_message_error != message:
                send_message(bot, message)
                check_message_error = message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        filename='main.log',
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s - %(lineno)d',
        level=logging.INFO)
    main()
