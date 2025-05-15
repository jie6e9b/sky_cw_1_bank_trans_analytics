import json
import logging
import os
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


def get_high_cashback_categories(df: pd.DataFrame, year: str, month: str) -> str:
    """ Анализирует выгодные категории повышенного кешбэка за указанный месяц.
    Args: year (str): Год в формате YYYY.
          month (str): Месяц в формате MM.
          df (pandas.DataFrame): DataFrame с данными о расходах
    Returns: str: JSON-ответ с прогнозом начисленного кешбэка по категориям."""

    logger.debug("Запуск функции get_high_cashback_categories")
    # Проверка входных данных
    if df is None or df.empty:
        logger.error("Пустой список транзакций передан в функцию.")
        return json.dumps({"error": "Нет данных для анализа."}, ensure_ascii=False)

    try:
        # Проверка наличия необходимых столбцов
        required_columns = ["Дата операции", "Сумма платежа", "Категория", "Сумма операции с округлением"]
        for column in required_columns:
            if column not in df.columns:
                logger.error(f"Ошибка. Отсутствует необходимый столбец: {column}")
                return json.dumps({"error": f"Отсутствует необходимый столбец: {column}"}, ensure_ascii=False)

        # Преобразование дат в столбце "Дата операции" в формат datetime
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True, errors='coerce')
        logger.debug("Транзакции успешно преобразованы в DataFrame.")

        # Проверка на наличие NaT после преобразования
        if df["Дата операции"].isna().any():
            logger.warning("Некоторые даты не удалось преобразовать в формат datetime")

        # Выборка транзакций за заданный месяц определенного года
        try:
            year_int = int(year)
            month_int = int(month)
        except ValueError:
                logger.error(f"Ошибка при преобразовании года ({year}) или месяца ({month}) в число")
                return json.dumps({"error": "Некорректный формат года или месяца"}, ensure_ascii=False)

        slice_df = df[(df["Дата операции"].dt.month == month_int) & (df["Дата операции"].dt.year == year_int)]

        if slice_df.empty:
            logger.info(f"Нет данных за месяц {month} (год {year}).")
            return json.dumps({"info": f"Нет данных за месяц {month} (год {year})"}, ensure_ascii=False)

        logger.info(f"Сделана выборка транзакций за месяц {month} (год {year}).")

        # DataFrame только с расходами (исключая переводы)
        spent_df = slice_df[(slice_df["Сумма платежа"] < 0) &
                            (slice_df["Категория"] != "Переводы") &
                            (slice_df["Категория"] != "Наличные")]

        if spent_df.empty:
            logger.info(f"Нет расходов за месяц {month} (год {year}).")
            return json.dumps({"info": f"Нет расходов за месяц {month} (год {year})"}, ensure_ascii=False)

        # Группировка данных по категориям трат
        category_grouped = spent_df.groupby(by="Категория", as_index=False)
        # for name, group in category_grouped:
        #     print(f"Категория: {name}")
        #     print(group)
        #     print("-" * 50)

        # Расчет сумм расходов по каждой категории
        category_sum = category_grouped["Сумма операции с округлением"].sum()
        # for index, row in category_sum.iterrows():
        #     formatted_sum = f"{row['Сумма операции с округлением']:,.2f}".replace(",", " ")
        #     print(f"Категория: {row['Категория']:<20} Сумма: {formatted_sum} руб.")

        # Сортировка сумм расходов по каждой категории по убыванию
        sorted_category_sum = category_sum.sort_values(
            by="Сумма операции с округлением",
            ascending=False,
            ignore_index=True
        )

        # Формирование результата
        result = {
            "period": f"{year}-{month}",
            "cashback_analysis": {}
        }

        # Стандартный процент кешбэка
        standard_cashback_rate = 0.01  # 1%

        # Формирование данных для вывода сводной информации по каждой категории
        for index, row in sorted_category_sum.iterrows():
            category = row["Категория"]
            spent_amount = abs(row["Сумма операции с округлением"])  # Берем абсолютное значение для удобства
            potential_cashback = round(spent_amount * standard_cashback_rate, 2)

            result["cashback_analysis"][category] = {
                "total_spent": float(spent_amount),
                "cashback_rate": float(standard_cashback_rate),
                "potential_cashback": float(potential_cashback)
            }

            logger.debug("Сводная информация о кешбэке по каждой категории успешно получена.")

        return json.dumps(result, indent=4, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Произошла ошибка при анализе данных: {str(e)}")
        return json.dumps({"error": f"Произошла ошибка при анализе данных: {str(e)}"}, ensure_ascii=False)
