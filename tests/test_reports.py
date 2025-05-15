import pandas as pd
import json
from datetime import datetime
from src.reports import spending_by_category

def test_spending_by_category_valid():
    data = {
        "Дата операции": ["01.04.2024", "15.04.2024", "01.03.2024"],
        "Сумма платежа": [-100.0, -200.0, -50.0],
        "Категория": ["Продукты", "Продукты", "Кафе"],
        "Описание": ["Пятёрочка", "Магнит", "Starbucks"]
    }
    df = pd.DataFrame(data)

    result = spending_by_category(df, category="Продукты", start_date="30.04.2024")
    assert '"Продукты"' in result
    assert "Пятёрочка" in result
    assert "Магнит" in result


def test_spending_by_category_no_data_in_category():

    data = {
        "Дата операции": ["01.04.2024"],
        "Сумма платежа": [-100.0],
        "Категория": ["Кафе"],
        "Описание": ["Starbucks"]
    }
    df = pd.DataFrame(data)

    result = spending_by_category(df, category="Продукты", start_date="30.04.2024")
    assert result == json.dumps({"Продукты": []}, ensure_ascii=False, indent=4)

def test_spending_by_category_boundary_date():

    start_date = datetime.strptime("30.04.2024", "%d.%m.%Y")
    boundary_date = (start_date - pd.Timedelta(days=90)).strftime("%d.%m.%Y")

    df = pd.DataFrame({
        "Дата операции": [boundary_date],
        "Сумма платежа": [-150.0],
        "Категория": ["Продукты"],
        "Описание": ["Перекрёсток"]
    })

    result = spending_by_category(df, category="Продукты", start_date=start_date)
    assert "Перекрёсток" in result

def test_spending_by_category_invalid_date_format():

    df = pd.DataFrame(columns=["Дата операции", "Сумма платежа", "Категория"])
    result = spending_by_category(df, category="Продукты", start_date="не дата")

    assert "error" in result