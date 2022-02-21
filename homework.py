import json
import logging
import os
import time

import exceptions as UserExceptions
import requests
import telegram

from dotenv import load_dotenv
from http import HTTPStatus
from typing import Optional

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)

formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s'
)

handler.setFormatter(formatter)

PRACTICUM_TOKEN: Optional[str] = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: Optional[str] = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot: telegram.bot.Bot, message: str):
    """Send message."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.TelegramError as error:
        raise UserExceptions.MessageNotSend(
            f'Message does not send. Error: {error}'
        )


def get_api_answer(current_timestamp: int) -> dict:
    """Get API answer."""
    timestamp: int = current_timestamp or int(time.time())
    params: dict = {'from_date': timestamp}

    try:
        homework_statuses: requests.models.Response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except requests.exceptions.RequestException as error:
        logger.error(f'Ошибка при отправке запроса: {error}')
    else:
        if homework_statuses.status_code != HTTPStatus.OK:
            logger.error(
                f'Недоступность эндпоинта {ENDPOINT}'
                f'Код ответа API {homework_statuses.status_code}'
            )
            raise UserExceptions.StatusCodeNotOK(
                'Not allowed. Code is not OK.'
            )
    try:
        return homework_statuses.json()
    except json.decoder.JSONDecodeError as error:
        raise UserExceptions.JSONDecodeError(f'Occurs {error}')
            


def check_response(response: dict) -> list:
    """Check response."""
    try:
        list_of_homeworks: list = response['homeworks']
    except TypeError:
        logger.critical('Dictionary is empty.')
        raise TypeError('Dictionary is empty.')
    except KeyError:
        logger.critical('Ответ от API не содержит ключа `homeworks`.')
        raise KeyError('Ответ от API не содержит ключа `homeworks`.')
    else:
        if not isinstance(list_of_homeworks, list):
            raise UserExceptions.ListHWIsNotList('HW list is not a list.')
    return list_of_homeworks


def parse_status(homework: dict) -> str:
    """Parse status."""
    try:
        homework_name: Optional[str] = homework['homework_name']
        homework_status: Optional[str] = homework['status']
    except KeyError as error:
        raise KeyError(f'Homework does not contain data: {error}')
    try:
        verdict: str = HOMEWORK_STATUSES[f'{homework_status}']
    except UnboundLocalError as error:
        logger.error(
            'Недокументированный статус домашней работы,'
            'обнаруженный в ответе API'
            f'Ошибка: {error}'
        )
        return f'Ошибка {error}'
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Check tokens."""
    if (PRACTICUM_TOKEN is None or TELEGRAM_TOKEN is None or TELEGRAM_CHAT_ID
       is None):
        return False
    return True


def main():
    """How does the bot work. Main logic."""
    if not check_tokens():
        logger.critical(
            'Отсутствие обязательных переменных окружения'
            'во время запуска бота'
        )
        raise Exception('Tokens is unavailiable.')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp: int = int(time.time())

    while True:
        try:
            response: dict = get_api_answer(current_timestamp)
            homeworks_list: list = check_response(response)

            try:
                message: str = parse_status(homeworks_list[0])
                send_message(bot, message)
                logger.info('Удачная отправка сообщения в Telegram')
            except IndexError:
                logger.debug('Отсутствие в ответе новых статусов')

            current_timestamp: int = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message: str = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            logger.error('Cбой при отправке сообщения в Telegram')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
