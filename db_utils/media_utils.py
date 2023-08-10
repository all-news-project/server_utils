from typing import Union, List

from db_driver import get_current_db_driver, DBConsts
from db_driver.utils.exceptions import DataNotFoundDBException
from db_utils.general_db_utils import GeneralDBUtils
from logger import get_current_logger


class MediaUtils:
    def __init__(self):
        self.logger = get_current_logger()
        self._db = get_current_db_driver()
        self._general_db_utils = GeneralDBUtils()

    def get_google_article_icon_url(self, media: str) -> Union[str, None]:
        try:
            data_filter = {"media": media}
            data_dict = self._db.get_one(table_name=DBConsts.MEDIA_TABLE_NAME, data_filter=data_filter)
            url = data_dict["src"]
            self.logger.info(f"Got icon url of media `{media}` -> `{url}`")
            return url
        except DataNotFoundDBException:
            self.logger.warning(f"Didn't find url icon for media `{media}`")
            return None
        except Exception as e:
            desc = f"Error getting icon url for media `{media}`, except: {str(e)}"
            self.logger.error(desc)
            raise e

    def get_media_list(self) -> List[str]:
        media_list = []
        media = self._general_db_utils.get_all_collection_data(table_name="media")
        for media_data in media:
            media_list.append(media_data.get("media"))
        return media_list
