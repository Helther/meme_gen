from abc import ABC, abstractmethod
import requests
import os
from enum import Enum

"""
In order to add new API update API enum and create_api_from_config factory
with newly created class 
"""
class API(Enum):
    mattermost = 0


class Messenger(ABC):

    def __init__(self, server_url) -> None:
        self.server_url = server_url

    @abstractmethod
    def login(self, auth_info) -> None:
        """first handle authentification"""
        pass

    @abstractmethod
    def upload_files(self, file_paths: list[str], chat_info) -> None:
        """then, provided file_paths upload them to messenger servers and get back response info"""
        pass

    @abstractmethod
    def post_message(self, chat_info, message: str) -> None:
        """finally post desired msg to the specified chat"""
        pass


class MattermostApi(Messenger):
        
    def __init__(self, server_url) -> None:
        Messenger.__init__(self, server_url)
        self.token = None
        self.file_ids = []

    def login(self, auth_info) -> None:
        auth_login, auth_pass = auth_info
        url = self.server_url + "/api/v4/users/login"
        data = {"login_id": auth_login, "password": auth_pass}

        resp: requests.Response = requests.post(url, json = data)
        self.token = resp.headers.get("Token", None)
        if not resp.ok or not self.token:
            raise Exception("Falied to login to server")

    def upload_files(self, file_paths: list[str], chat_info) -> None:
        if not self.token:
            raise Exception("Not signed in")

        url = self.server_url + "/api/v4/files?channel_id=" + chat_info
        headers = {"Authorization": f"Bearer {self.token}"}
        resp: requests.Response = requests.post(url, headers=headers, files={os.path.basename(file): open(file, "rb") for file in file_paths})
        if not resp.ok:
            raise Exception("Falied to upload file")

        file_infos = resp.json().get("file_infos")
        if not file_infos:
            raise Exception("Invalid file infos")

        file_ids = []
        for i in range(len(file_paths)):
            file_ids.append(file_infos[i]["id"])
        self.file_ids = file_ids

    def post_message(self, chat_info, message: str) -> None:
        if not self.token:
            raise Exception("Not signed in")

        url = self.server_url + "/api/v4/posts"
        data = {"channel_id": chat_info, "message": message, "file_ids": self.file_ids}
        headers = {"Authorization": f"Bearer {self.token}"}
        resp: requests.Response = requests.post(url, json = data, headers=headers)
        if not resp.ok:
            raise Exception("Falied to post msg")


def create_api_from_config(api_config, server_url: str) -> Messenger:
    if api_config == API.mattermost.name:
        return MattermostApi(server_url)
    
    raise Exception("Invalid messenger config")
