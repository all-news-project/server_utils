import os
import threading
from datetime import datetime
from time import sleep
from typing import List

import requests
import schedule

from db_driver.insterfaces.interface_db_driver import DBDriverInterface
from db_driver.utils.consts import DBObjectsConsts, DBConsts
from db_driver.utils.exceptions import ErrorConnectDBException, DataNotFoundDBException
from logger import get_current_logger, log_function
from singleton_class import Singleton
from bson.objectid import ObjectId


class GitDBDriver(DBDriverInterface, Singleton):
    DB_NAME = os.getenv(key='DB_NAME', default='git')
    REFRESH_DB_DATA_TIMEOUT = int(os.getenv(key="REFRESH_DB_DATA_TIMEOUT", default=10))

    def __init__(self):
        self.logger = get_current_logger()
        self._in_collecting_data_process = False
        self.__db = dict()
        initial_collection = threading.Thread(target=self.refresh_db_data)
        initial_collection.start()
        schedule.every(self.REFRESH_DB_DATA_TIMEOUT).minutes.do(self.refresh_db_data)
        self.scheduler = threading.Thread(target=self._run_scheduler_refresh_data)
        self.scheduler.start()
        initial_collection.join()
        self.logger.debug(f"Connected to gitdb")

    @staticmethod
    def _run_scheduler_refresh_data():
        while True:
            schedule.run_pending()
            sleep(1)

    @log_function
    def __connect_to_db(self):
        self._in_collecting_data_process = True
        for collection in DBConsts.GIT_DB_COLLECTIONS:
            try:
                self.logger.debug(msg=f"Trying to get db data for `{collection}`")
                url = f"{DBConsts.GIT_DB_URL}{collection}.json"
                self.logger.debug(msg=f"Requests from -> {url}")
                headers = {'Content-type': 'application/json;'}
                res = requests.get(url=url, headers=headers)
                res_json = res.json()
                if collection in DBObjectsConsts.DATETIME_ATTRIBUTES.keys():
                    date_time_attributes = DBObjectsConsts.DATETIME_ATTRIBUTES[collection]
                    for document in res_json:
                        for date_time_attribute in date_time_attributes:
                            if document[date_time_attribute] and isinstance(document[date_time_attribute], str):
                                document[date_time_attribute] = datetime.fromisoformat(document[date_time_attribute])
                self.__db[collection] = res_json
                self.logger.info(f"Done collect data from git db for `{collection}`, Got {len(res_json)}")
            except Exception as e:
                desc = f"Error getting git db data for `{collection}`, except: {str(e)}"
                self.logger.error(desc)
                self._in_collecting_data_process = False
                raise ErrorConnectDBException(desc)
        self.logger.info(f"Done getting collections data of: `{DBConsts.GIT_DB_COLLECTIONS}`")
        self._in_collecting_data_process = False

    @log_function
    def refresh_db_data(self):
        self.logger.debug(f"Refreshing db data...")
        if not self._in_collecting_data_process:
            self.__connect_to_db()

    @log_function
    def get_one(self, table_name: str, data_filter: dict) -> dict:
        try:
            self.logger.debug(f"Trying to get one data from table: '{table_name}', db: '{self.DB_NAME}'")
            for document in self.__db[table_name]:
                for key, value in data_filter.items():
                    if document[key] and document[key] == value:
                        self.logger.info(f"Got data from db: '{self.DB_NAME}', table_name: '{table_name}''")
                        return document

            desc = f"Error find data with filter: {data_filter}, table: '{table_name}', db: '{self.DB_NAME}'"
            self.logger.warning(desc)
            raise DataNotFoundDBException(desc)
        except Exception as e:
            self.logger.error(f"Error get one from db - {str(e)}")
            raise e

    @log_function
    def get_many(self, table_name: str, data_filter: dict) -> List[dict]:
        try:
            self.logger.debug(f"Trying to get one data from table: '{table_name}', db: '{self.DB_NAME}'")
            documents = []
            for document in self.__db[table_name]:
                for key, value in data_filter.items():
                    if not document[key]:
                        continue
                    if isinstance(value, dict):
                        if "$in" in value.keys():
                            if any([document[key] == single_value for single_value in value["$in"]]):
                                documents.append(document)
                    elif document[key] == value:
                        documents.append(document)

            if documents:
                self.logger.info(f"Got {len(documents)} data from db: '{self.DB_NAME}', table_name: '{table_name}'")
                return documents
            else:
                desc = f"Error find data with filter: {data_filter}, table: '{table_name}', db: '{self.DB_NAME}'"
                self.logger.warning(desc)
                raise DataNotFoundDBException(desc)
        except Exception as e:
            self.logger.error(f"Error get one from db - {str(e)}")
            raise e

    @log_function
    def count(self, table_name: str, data_filter: dict) -> int:
        try:
            return len(self.get_many(table_name=table_name, data_filter=data_filter))
        except DataNotFoundDBException:
            return 0

    @log_function
    def exists(self, table_name: str, data_filter: dict) -> bool:
        try:
            return self.get_one(table_name=table_name, data_filter=data_filter) is not None
        except DataNotFoundDBException:
            return False

    @log_function
    def delete_one(self, table_name: str, data_filter: dict) -> bool:
        raise NotImplementedError(DBConsts.GIT_DB_DELETE_ERROR_MSG)

    @log_function
    def delete_many(self, table_name: str, data_filter: dict) -> int:
        raise NotImplementedError(DBConsts.GIT_DB_DELETE_ERROR_MSG)

    def insert_one(self, table_name: str, data: dict) -> ObjectId:
        raise NotImplementedError(DBConsts.GIT_DB_INSERT_ERROR_MSG)

    def insert_many(self, table_name: str, data_list: List[dict]) -> List[ObjectId]:
        raise NotImplementedError(DBConsts.GIT_DB_INSERT_ERROR_MSG)

    def update_one(self, table_name: str, data_filter: dict, new_data: dict) -> ObjectId:
        raise NotImplementedError(DBConsts.GIT_DB_UPDATE_ERROR_MSG)

    def update_many(self, table_name: str, data_filter: dict, new_data: dict) -> List[ObjectId]:
        raise NotImplementedError(DBConsts.GIT_DB_UPDATE_ERROR_MSG)
