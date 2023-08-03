import os
from typing import Union

import requests

from logger import get_current_logger
from server_consts import FileUtilsConsts


class FileUtils:
    def __init__(self):
        self.logger = get_current_logger()

    def save_image_from_url(
            self, url: str, image_name: str, path: str = FileUtilsConsts.SAVE_IMG_PATH) -> Union[str, None]:
        """
        This function saving image from url to a file
        :param url:
        :param image_name:
        :param path:
        :return:
        """
        try:
            file_path = os.path.join(path, image_name)
            r = requests.get(url, stream=True)
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)
            self.logger.info(f"Saved image to -> `{file_path}`")
            return file_path
        except Exception as e:
            print(f"Error saving image from `{url}`, except: {str(e)}")
            return None
