from typing import Any, List

from db_driver import get_current_db_driver
from logger import get_current_logger


class GeneralDBUtils:
    def __init__(self):
        self.logger = get_current_logger()
        self._db = get_current_db_driver()

    def remove_duplicates_by_field(self, table_name: str, field_name: str):
        unique_data = self.get_all_unique_values_by_field(table_name=table_name, field_name=field_name)
        for data in unique_data:
            count = self._db.count(table_name=table_name, data_filter={field_name: data})
            self.logger.info(f"Found {count} of data filter: {field_name}:{data}")
            while count > 1:
                self._db.delete_one(table_name=table_name, data_filter={field_name: data})
                count -= 1

    def get_all_unique_values_by_field(self, table_name: str, field_name: str) -> List[Any]:
        all_data = self.get_all_collection_data(table_name=table_name)
        field_data = set()
        for data in all_data:
            field_data.add(data[field_name])
        return list(field_data)

    def get_all_collection_data(self, table_name) -> List[dict]:
        return self._db.get_many(table_name=table_name, data_filter={})


if __name__ == '__main__':
    general_db_utils = GeneralDBUtils()
    general_db_utils.remove_duplicates_by_field(table_name="media", field_name="src")