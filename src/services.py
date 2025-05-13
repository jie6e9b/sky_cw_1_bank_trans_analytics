import json
import logging
import os
from datetime import datetime
from typing import List, Dict

import pandas as pd


def setup_logger() -> logging.Logger:
    """Настраивает логгер для модуля services."""
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "services.log")

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


def get_high_cashback_categories(year: str, month: str, transactions: List[Dict]) -> str:
    """ Анализирует выгодные категории повышенного кешбэка за указанный месяц и год.
    Args: year (str): Год в формате YYYY.
          month (str): Месяц в формате MM.
          transactions (List[Dict]): Список транзакций (словарей).
    Returns: str: JSON-ответ с прогнозом начисленного кешбэка по категориям."""

    logger.debug("Запуск функции get_high_cashback_categories")

    if not transactions:
        logger.warning("Пустой список транзакций передан в функцию.")
        return json.dumps({"error": "Нет данных для анализа."}, ensure_ascii=False)

    try:
        df = pd.DataFrame(transactions)
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
        logger.info("Транзакции успешно преобразованы в DataFrame.")
    except Exception as e:
        logger.error(f"Ошибка при преобразовании транзакций: {e}")
        return json.dumps({"error": "Ошибка обработки данных."}, ensure_ascii=False)

    try:
        month_int = int(month)
        year_int = int(year)
        logger.debug(f"Анализ за {month_int:02d}.{year_int}")
    except ValueError:
        logger.error("Неверный формат месяца или года.")
        return json.dumps({"error": "Неверный формат месяца или года."}, ensure_ascii=False)

    # Отбор транзакций за указанный месяц
    df_period = df[
        (df["Дата операции"].dt.month == month_int) & (df["Дата операции"].dt.year == year_int)
    ]

    if df_period.empty:
        logger.info("Нет транзакций за указанный период.")
        return json.dumps({"info": "Нет транзакций за указанный месяц."}, ensure_ascii=False)

    # Фильтр: только траты, не переводы
    spent_df = df_period[
        (df_period["Сумма платежа"] < 0) & (df_period["Категория"] != "Переводы")
    ]

    if spent_df.empty:
        logger.info("Нет расходов, подходящих для анализа кешбэка.")
        return json.dumps({"info": "Нет расходов для анализа кешбэка."}, ensure_ascii=False)

    grouped = (
        spent_df.groupby("Категория", as_index=False)["Сумма операции с округлением"]
        .sum()
        .sort_values(by="Сумма операции с округлением", ascending=False, ignore_index=True)
    )

    result = {
        row["Категория"]: round(row["Сумма операции с округлением"] * 0.01, 2)
        for _, row in grouped.iterrows()
    }

    logger.info("Расчет кешбэка по категориям успешно завершён.")
    return json.dumps(result, indent=4, ensure_ascii=False)
