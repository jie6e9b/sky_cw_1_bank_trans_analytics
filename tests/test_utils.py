import json
from datetime import datetime
from unittest.mock import mock_open, patch

import pandas as pd
import pytest

from src.utils import (
    actual_currencies,
    actual_stocks,
    get_date_range,
    get_slice_of_data,
    get_summary_card_data,
    get_time_for_greeting,
    read_data_file,
    top_5_transactions_by_sum,
)


def test_get_date_range_success(test_date):
    expected = (datetime(2023, 5, 1, 0, 0, 0), datetime(2023, 5, 15, 14, 30, 0))
    assert get_date_range(test_date) == expected


def test_read_data_file_empty():
    with patch("pandas.read_excel", return_value=pd.DataFrame()):
        result = read_data_file()
        assert isinstance(result, pd.DataFrame)
        assert result.empty


def test_get_slice_of_data_success(sample_dataframe):
    with patch("src.utils.read_data_file", return_value=sample_dataframe):
        result = get_slice_of_data(datetime(2025, 1, 1), datetime(2025, 1, 31))
        assert len(result) == 2
        assert result["Дата операции"].min().date() >= datetime(2025, 1, 1).date()
        assert result["Дата операции"].max().date() <= datetime(2025, 1, 31).date()


def test_get_slice_of_data_empty_result(sample_dataframe):
    with patch("src.utils.read_data_file", return_value=sample_dataframe):
        result = get_slice_of_data(datetime(2025, 10, 1), datetime(2025, 12, 30))
        assert result.empty


def test_get_slice_of_data_empty_input():
    with patch("src.utils.read_data_file", return_value=pd.DataFrame()):
        result = get_slice_of_data(datetime(2025, 1, 1), datetime(2025, 1, 30))
        assert result.empty


@pytest.mark.parametrize(
    "hour, expected_greeting",
    [
        (4, "Доброй ночи!"),
        (5, "Доброе утро!"),
        (11, "Доброе утро!"),
        (12, "Добрый день!"),
        (17, "Добрый день!"),
        (18, "Добрый вечер!"),
        (22, "Добрый вечер!"),
        (23, "Доброй ночи!"),
        (0, "Доброй ночи!"),
    ],
)
def test_get_time_for_greeting(hour, expected_greeting):
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2023, 1, 1, hour)
        assert get_time_for_greeting() == expected_greeting


def test_get_summary_card_data_success(sample_data_with_cards):
    expected = [
        {"last_digits": "2222", "total_spent": 2000.0, "cashback": 20.0},
        {"last_digits": "3333", "total_spent": 1500.0, "cashback": 15.0},
        {"last_digits": "5678", "total_spent": 1500.0, "cashback": 15.0},
    ]
    result = get_summary_card_data(sample_data_with_cards)
    assert result == expected


def test_get_summary_card_data_empty():
    result = get_summary_card_data(pd.DataFrame())
    assert result == []


def test_top_5_transactions_by_sum_success(sample_data_for_top_5_transactions):
    result = top_5_transactions_by_sum(sample_data_for_top_5_transactions)
    assert isinstance(result, list)
    assert len(result) == 5
    assert all(t["category"] != "Супермаркеты" for t in result)


def test_top_5_transactions_by_sum_empty():
    assert top_5_transactions_by_sum(pd.DataFrame()) == []


def test_top_5_transactions_by_sum_failed_status_only(sample_data_for_top_5_transactions_failed_status):
    assert top_5_transactions_by_sum(sample_data_for_top_5_transactions_failed_status) == []

# ------------------------------------------------------------------------------------
# actual_currencies

def test_actual_currencies_success(mock_user_settings_for_currencies, mock_api_response_for_currencies):
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_user_settings_for_currencies))):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_api_response_for_currencies

            result = actual_currencies()

            assert result == [
                {"currency": "USD", "rate": round(1 / 0.013, 2)},
                {"currency": "EUR", "rate": round(1 / 0.011, 2)},
                {"currency": "GBP", "rate": round(1 / 0.0095, 2)},
            ]


def test_actual_currencies_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        assert actual_currencies() == []


def test_actual_currencies_invalid_json():
    with patch("builtins.open", mock_open(read_data="INVALID")):
        assert actual_currencies() == []


def test_actual_stocks_success(mock_user_settings_for_stocks, mock_api_response_for_stocks):
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_user_settings_for_stocks))):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_api_response_for_stocks

            result = actual_stocks()

            assert result == [
                {"stock": "AAPL", "price": 150.12},
                {"stock": "GOOGL", "price": 2750.45},
                {"stock": "MSFT", "price": 305.67},
            ]


def test_actual_stocks_file_not_found():
    with patch("builtins.open", side_effect=FileNotFoundError):
        assert actual_stocks() == []


def test_actual_stocks_invalid_json():
    with patch("builtins.open", mock_open(read_data="INVALID")):
        assert actual_stocks() == []