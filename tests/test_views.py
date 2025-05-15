import json
import pytest

from src.views import main_info

def test_main_info_success(valid_date_str, mock_dependencies):
    """Тест успешного выполнения main_info"""
    result_json = main_info(valid_date_str)
    result = json.loads(result_json)

    assert isinstance(result, dict)
    assert "greeting" in result
    assert "cards" in result
    assert "top_transactions" in result
    assert "currency_rates" in result
    assert "stock_prices" in result

    assert result["greeting"] == "Добрый день!"
    assert isinstance(result["cards"], list)
    assert isinstance(result["top_transactions"], list)
    assert isinstance(result["currency_rates"], list)
    assert isinstance(result["stock_prices"], list)


def test_main_info_invalid_date_format():
    """Тест ошибки при неверном формате даты"""
    invalid_date_str = "01-05-2025 12:00:00"
    with pytest.raises(ValueError, match="Ожидаемый формат даты: 'YYYY-MM-DD HH:MM:SS'"):
        main_info(invalid_date_str)