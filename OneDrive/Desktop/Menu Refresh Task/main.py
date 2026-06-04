from src.merge_data import merge_datasets
from src.menu_item_intelligence import run_menu_item_intelligence
from src.export_summary import run_final_recommendation_exports

def main():
    merge_datasets()
    run_menu_item_intelligence()
    run_final_recommendation_exports()


if __name__ == "__main__":
    main()
