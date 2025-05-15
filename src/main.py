from src.reports import spending_by_category
from src.services import get_high_cashback_categories
from src.utils import read_data_file
from src.views import main_info

if __name__ == "__main__":

    df = read_data_file()

    result_views = main_info("2021-04-10 20:30:00")
    print(result_views)

    result_reports = spending_by_category(df, "Топливо", "01.02.2018")
    print(result_reports)

    result_services = get_high_cashback_categories(df,"2021", "05")
    print(result_services)

