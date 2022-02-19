import logging
import os
import time

import requests
import telegram

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)

formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s'
)

handler.setFormatter(formatter)

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

BOT = telegram.Bot(token=TELEGRAM_TOKEN)


def send_message(bot: telegram.bot, message: str):
    """Send message."""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp: int) -> dict:
    """Get API answer."""
    timestamp: int = current_timestamp or int(time.time())
    params: dict = {'from_date': timestamp}

    try:
        homework_statuses: requests = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except Exception as error:
        logger.error(f'Ошибка при отправке запроса: {error}')
    else:
        if homework_statuses.status_code != 200:
            logger.error(
                f'Недоступность эндпоинта {ENDPOINT}'
                f'Код ответа API {homework_statuses.status_code}'
            )
            raise TypeError("asd")
    return homework_statuses.json()


def check_response(response: dict) -> list:
    """Check response."""
    if len(response) == 0:
        logger.critical('Ошибка')
        raise IndexError("asd")
    elif 'homeworks' not in response:
        logger.error('отсутствие ожидаемых ключей в ответе API ')
        raise TypeError('homework not in a dictionary')
    try:
        list_of_homeworks: list = response.get('homeworks')
        if isinstance(list_of_homeworks, dict):
            raise TypeError('not list')
        return list_of_homeworks
    except Exception as error:
        logger.critical(f'Вид ошибки: {error}')
        send_message(BOT, f'Ошибка {error}')


def parse_status(homework: dict) -> str:
    """Parse status."""
    homework_name: str = homework.get('homework_name')
    homework_status: str = homework.get('status')

    try:
        verdict: str = HOMEWORK_STATUSES[homework_status]
    except UnboundLocalError as error:
        logger.error(
            'Недокументированный статус домашней работы,'
            'обнаруженный в ответе API'
            f'Ошибка: {error}'
        )
        send_message(BOT, f'Ошибка {error}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Check tokens."""
    if (PRACTICUM_TOKEN is None or TELEGRAM_TOKEN is None or TELEGRAM_CHAT_ID
       is None):
        return False
    return True


def main():
    """How does the bot work. Main logic."""
    if check_tokens() is False:
        logger.critical(
            'Отсутствие обязательных переменных окружения'
            'во время запуска бота'
        )

    current_timestamp: int = int(time.time())

    while True:
        try:
            response: dict = get_api_answer(current_timestamp)
            homeworks_list: list = check_response(response)

            try:
                message: str = parse_status(homeworks_list[0])
                send_message(BOT, message)
                logger.info('Удачная отправка любого сообщения в Telegram')
            except IndexError:
                logger.debug('Отсутствие в ответе новых статусов')
                send_message(BOT, 'Список пуст')
            current_timestamp: int = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message: str = f'Сбой в работе программы: {error}'
            send_message(BOT, message)
            logger.error('Cбой при отправке сообщения в Telegram')
            time.sleep(RETRY_TIME)
        else:
            pass


if __name__ == '__main__':
    main()
