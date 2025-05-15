import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Union

import pandas as pd


def setup_logger() -> logging.Logger:
    """Настраивает логгер для модуля reports."""
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "reports.log")

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s - %(filename)s - %(funcName)s - %(levelname)s: %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


logger = setup_logger()


def spending_by_category(
        transactions: pd.DataFrame,
        category: str,
        start_date: Optional[Union[str, datetime]] = None
) -> str:
    """ Возвращает JSON-отчёт о расходах по указанной категории за 3 месяца до заданной даты.
    :param transactions: DataFrame с транзакциями.
    :param category: Название категории.
    :param start_date: Строка в формате 'ДД.ММ.ГГГГ' или datetime (по умолчанию текущая дата).
    :return: JSON-строка с расходами по дате и сумме."""

    try:
        if start_date is None:
            start_dt = datetime.now()
        elif isinstance(start_date, str):
            start_dt = datetime.strptime(start_date, '%d.%m.%Y')
        else:
            start_dt = start_date

        end_dt = start_dt - timedelta(days=90)

        transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], dayfirst=True)

        mask = transactions["Дата операции"].between(end_dt, start_dt)
        filtered_df = transactions[mask]
        logger.debug(f"Фильтрация по датам: {end_dt.strftime('%d.%m.%Y')} — {start_dt.strftime('%d.%m.%Y')}")

        # Оставляем только расходы и нужную категорию
        spent_df = filtered_df[
            (filtered_df["Сумма платежа"] < 0) & (filtered_df["Категория"] == category)
            ]

        if spent_df.empty:
            logger.info(f"Нет трат в категории '{category}' за указанный период.")
            return json.dumps({category: []}, ensure_ascii=False, indent=4)

        result = [
            {
                "Дата операции": row["Дата операции"].strftime("%Y-%m-%d"),
                "Сумма платежа": round(row["Сумма платежа"], 2),
                "Описание": row.get("Описание", "")
            }
            for _, row in spent_df.iterrows()
        ]

        logger.info(f"Получены траты по категории '{category}' — {len(result)} записей.")
        return json.dumps({category: result}, ensure_ascii=False, indent=4)

    except Exception as e:
        logger.error(f"Ошибка в функции spending_by_category: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=4)
