import json
import logging
import os
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv

PATH_TO_EXCEL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "operations.xlsx")
PATH_TO_USER_SETTINGS_JSON = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_settings.json")


def setup_logger() -> logging.Logger:
    """Настраивает логгер для модуля utils."""
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_path = os.path.join(logs_dir, "utils.log")

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


def get_date_range(date_time: str) -> tuple[datetime, datetime]:
    end_date = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
    start_date = end_date.replace(day=1, hour=0, minute=0, second=0)
    logger.debug("Определен период времени для выборки транзакций.")
    return start_date, end_date


def read_data_file() -> pd.DataFrame:
    df_excel = pd.read_excel(PATH_TO_EXCEL, sheet_name="Отчет по операциям")
    if df_excel.empty:
        print("Ошибка. Данные для анализа не обнаружены.")
        return pd.DataFrame()
    df_excel["Номер карты"] = df_excel["Номер карты"].fillna("Карта не указана")
    logger.debug(f"Выполнено чтение файла {PATH_TO_EXCEL}.")
    return df_excel


def get_slice_of_data(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    df = read_data_file()
    if df.empty:
        print("Ошибка. Данные для анализа не обнаружены.")
        return pd.DataFrame()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    slice_df = df[df["Дата операции"].between(start_date, end_date)]
    logger.debug(f"Сделана выборка транзакций в диапазоне дат {start_date} - {end_date}.")
    return slice_df


def get_time_for_greeting() -> str:
    user_time_hour = datetime.now().hour
    logger.debug("Формируется приветствие для пользователя.")
    if 5 <= user_time_hour < 12:
        return "Доброе утро!"
    elif 12 <= user_time_hour < 18:
        return "Добрый день!"
    elif 18 <= user_time_hour < 23:
        return "Добрый вечер!"
    else:
        return "Доброй ночи!"


def get_summary_card_data(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        print("Ошибка. Данные для анализа не обнаружены.")
        return []
    spent_df = df[df["Сумма платежа"] < 0]
    card_grouped = spent_df.groupby(by="Номер карты", as_index=False)
    cards_sum = card_grouped["Сумма операции с округлением"].sum()

    result = []
    for _, row in cards_sum.iterrows():
        result.append(
            {
                "last_digits": row["Номер карты"].replace("*", ""),
                "total_spent": round(row["Сумма операции с округлением"], 2),
                "cashback": round(row["Сумма операции с округлением"] * 0.01, 2)
            }
        )
    logger.debug("Сводная информация по каждой карте успешно получена.")
    return result


def top_5_transactions_by_sum(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        print("Ошибка. Данные для анализа не обнаружены.")
        return []

    filter_ok_transactions = df[df["Статус"] == "OK"]
    if filter_ok_transactions.empty:
        print("Ошибка. После фильтрации по статусу операции данные для анализа не обнаружены.")
        return []

    sorted_by_sum_df = filter_ok_transactions.sort_values(by="Сумма операции с округлением", ascending=False)
    top_by_sum = sorted_by_sum_df.head(5)

    result = []
    for _, row in top_by_sum.iterrows():
        result.append(
            {
                "date": row["Дата операции"].strftime("%d.%m.%Y"),
                "amount": round(row["Сумма операции с округлением"], 2),
                "category": row["Категория"],
                "description": row["Описание"]
            }
        )
    logger.debug("ТОП-5 транзакций по сумме операции успешно получены.")
    return result


def actual_currencies(base_currency: str = "RUB") -> list[dict]:
    try:
        logger.debug("Чтение данных из JSON-файла...")
        with open(PATH_TO_USER_SETTINGS_JSON, "r") as file:
            currencies = json.load(file)["user_currencies"]
            logger.debug("Данные из JSON-файла успешно получены.")
    except json.JSONDecodeError:
        print("Ошибка декодирования файла.")
        logger.error("Произошла ошибка декодирования файла.")
        return []
    except FileNotFoundError:
        print(f"Ошибка! Файл по адресу {PATH_TO_USER_SETTINGS_JSON} не найден.")
        logger.error(f"Ошибка! Файл по адресу {PATH_TO_USER_SETTINGS_JSON} не найден.")
        return []

    url = "https://api.apilayer.com/exchangerates_data/latest"
    payload = {"symbols": ",".join(currencies), "base": base_currency}

    load_dotenv()
    api_key = os.getenv("API_KEY_APILAYER")
    headers = {"apikey": api_key}

    response = requests.get(url, headers=headers, params=payload)
    if response.status_code != 200:
        print(f"Неудачная попытка получить курс валют {currencies}. Возможная причина: {response.reason}.")
        logger.error(f"Неудачная попытка получить курсы валют {currencies}. Возможная причина: {response.reason}.")
        return []
    response_json = response.json()
    logger.debug(f"Курсы валют {currencies} по API-запросу успешно получены. Выполняется обработка данных.")

    result = []
    for key, value in response_json["rates"].items():
        result.append(
            {
                "currency": key,
                "rate": round(1 / value, 2)
            }
        )
    return result


def actual_stocks() -> list[dict]:
    try:
        logger.debug("Чтение данных из JSON-файла...")
        with open(PATH_TO_USER_SETTINGS_JSON, "r") as file:
            symbols = json.load(file)["user_stocks"]
            logger.info("Данные из JSON-файла успешно получены.")
    except json.JSONDecodeError:
        print("Ошибка декодирования файла.")
        logger.error("Произошла ошибка декодирования файла.")
        return []
    except FileNotFoundError:
        print(f"Ошибка! Файл по адресу {PATH_TO_USER_SETTINGS_JSON} не найден.")
        logger.error(f"Ошибка! Файл по адресу {PATH_TO_USER_SETTINGS_JSON} не найден.")
        return []

    url = "http://api.marketstack.com/v1/eod/latest"
    payload = {"symbols": ",".join(symbols)}

    load_dotenv()
    api_key = os.getenv("API_KEY_MARKETSTACK")
    headers = {"access_key": api_key}

    response = requests.get(url, params=payload, headers=headers)
    if response.status_code != 200:
        print(f"Неудачная попытка получить курсы акций {symbols}. Возможная причина: {response.reason}.")
        logger.error(f"Неудачная попытка получить курсы акций {symbols}. Возможная причина: {response.reason}.")
        return []
    response_json = response.json()
    logger.debug(f"Курсы акций {symbols} по API-запросу успешно получены. Выполняется обработка данных.")

    result = []
    for stock_info in response_json["data"]:
        result.append(
            {
                "stock": stock_info["symbol"],
                "price": stock_info["adj_close"]
            }
        )
    return result