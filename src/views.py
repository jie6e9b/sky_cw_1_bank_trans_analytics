import json
import logging
import os
from datetime import datetime
from typing import Dict

from src.utils import (
    actual_currencies,
    actual_stocks,
    get_date_range,
    get_slice_of_data,
    get_summary_card_data,
    get_time_for_greeting,
    top_5_transactions_by_sum,
)


def setup_logger() -> logging.Logger:
    """Настраивает логгер для модуля views."""
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file_path = os.path.join(logs_dir, "views.log")

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s - %(filename)s - %(funcName)s - %(levelname)s: %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


logger = setup_logger()


def main_info(date_time: str) -> str:
    """ Возвращает JSON с данными для страницы "Главная".
    Args: date_time (str): Дата и время в формате "YYYY-MM-DD HH:MM:SS".
    Returns: str: JSON-строка с приветствием, данными по картам, транзакциями, курсами валют и акциями"""

    logger.debug("Запуск функции main_info")

    try:
        datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
        logger.debug(f"Проверка формата даты прошла успешно: {date_time}")
    except ValueError as e:
        logger.error(f"Неверный формат даты: {date_time}")
        raise ValueError("Ожидаемый формат даты: 'YYYY-MM-DD HH:MM:SS'") from e

    start_date, end_date = get_date_range(date_time)
    logger.info(f"Выбран период: {start_date} — {end_date}")

    df = get_slice_of_data(start_date, end_date)
    logger.info(f"Получено {len(df)} транзакций за выбранный период")

    data: Dict[str, object] = {
        "greeting": get_time_for_greeting(),
        "cards": get_summary_card_data(df),
        "top_transactions": top_5_transactions_by_sum(df),
        "currency_rates": actual_currencies(),
        "stock_prices": actual_stocks(),
    }

    logger.info("Сформированы все блоки данных для главной страницы")
    return json.dumps(data, ensure_ascii=False, indent=4)
