import pytest
import pandas as pd
import json
from src.services import get_high_cashback_categories


@pytest.fixture
def base_df():
    return pd.DataFrame({
        "Дата операции": ["01.01.2024", "15.01.2024", "20.01.2024", "25.01.2024"],
        "Сумма платежа": [-1000, -500, -300, -200],
        "Категория": ["Продукты", "Кафе", "Продукты", "Наличные"],
        "Сумма операции с округлением": [-1000, -500, -300, -200]
    })


def test_valid_input(base_df):
    result = get_high_cashback_categories(base_df, "2024", "01")
    data = json.loads(result)
    assert "cashback_analysis" in data
    assert "Продукты" in data["cashback_analysis"]
    assert data["cashback_analysis"]["Продукты"]["total_spent"] == 1300.0


def test_invalid_date_format():
    df = pd.DataFrame({
        "Дата операции": ["не дата"],
        "Сумма платежа": [-100],
        "Категория": ["Кафе"],
        "Сумма операции с округлением": [-100]
    })
    result = get_high_cashback_categories(df, "2024", "01")
    data = json.loads(result)
    assert "info" in data or "error" in data


def test_empty_dataframe():
    df = pd.DataFrame()
    result = get_high_cashback_categories(df, "2024", "01")
    assert json.loads(result)["error"] == "Нет данных для анализа."


def test_missing_column(base_df):
    df = base_df.drop(columns=["Категория"])
    result = get_high_cashback_categories(df, "2024", "01")
    assert "error" in json.loads(result)


def test_no_transactions_in_month(base_df):
    result = get_high_cashback_categories(base_df, "2023", "12")
    assert "info" in json.loads(result)


def test_invalid_year_month(base_df):
    result = get_high_cashback_categories(base_df, "20xx", "01")
    assert "error" in json.loads(result)


def test_spent_only_excludes_cash_and_transfers():
    df = pd.DataFrame({
        "Дата операции": ["01.01.2024", "10.01.2024", "15.01.2024"],
        "Сумма платежа": [-1000, -300, -200],
        "Категория": ["Наличные", "Переводы", "Продукты"],
        "Сумма операции с округлением": [-1000, -300, -200]
    })
    result = get_high_cashback_categories(df, "2024", "01")
    data = json.loads(result)
    assert list(data["cashback_analysis"].keys()) == ["Продукты"]