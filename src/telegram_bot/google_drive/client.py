import logging
import os
from typing import Optional

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive, GoogleDriveFile

from .utils import create_keyfile_dict

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class GoogleDriveService:
    """Google Drive service class."""

    def __init__(self, client_json_file_path: Optional[str] = None):
        self.gauth = self.login_with_service_account(client_json_file_path)
        self.drive = GoogleDrive(self.gauth)

    def login_with_service_account(
        self, client_json_file_path: Optional[str] = None
    ) -> GoogleAuth:
        """
        Google Drive service with a service account.
        note: for the service account to work, you need to share the folder or
        files with the service account email.

        :return: google auth
        """
        try:
            settings = {"client_config_backend": "service"}

            if client_json_file_path:
                settings["service_config"] = {
                    "client_json_file_path": client_json_file_path
                }
            else:
                settings["service_config"] = {"client_json_dict": create_keyfile_dict()}

            gauth = GoogleAuth(settings=settings)
            gauth.ServiceAuth()
            return gauth
        except Exception as e:
            logging.error(f"Failed to authenticate with service account: {e}")
            raise

    def create_folder(
        self, folder_name: str, parent_folder_id: Optional[str] = None
    ) -> GoogleDriveFile:
        """
        Create a folder in the root directory or in a parent folder.
        """
        try:
            folder = self.drive.CreateFile(
                {"title": folder_name, "mimeType": "application/vnd.google-apps.folder"}
            )
            if parent_folder_id:
                folder["parents"] = [{"id": parent_folder_id}]
            folder.Upload()
            return folder
        except Exception as e:
            logging.error(f"Failed to create folder '{folder_name}': {e}")
            raise

    def get_folder_id(self, folder_name: str) -> Optional[str]:
        """
        Find the folder ID by its name.
        """
        try:
            folder_list = self.drive.ListFile(
                {
                    "q": f"title = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                }
            ).GetList()

            if folder_list:
                return folder_list[0]["id"]
            else:
                return None
        except Exception as e:
            logging.error(f"Failed to get folder ID for '{folder_name}': {e}")
            raise

    def get_file_by_title(self, file_name: str) -> Optional[str]:
        """
        Find the file ID by its name.
        """
        try:
            file_list = self.drive.ListFile(
                {"q": f"title = '{file_name}' and trashed = false"}
            ).GetList()

            if file_list:
                return file_list[0]
            else:
                return None

        except Exception as e:
            logging.error(f"Failed to get file ID for '{file_name}': {e}")
            raise

    def list_files_in_folder(self, folder_id: str) -> list[GoogleDriveFile]:
        """
        List all files in a folder by its ID.
        """
        try:
            file_list = self.drive.ListFile(
                {"q": f"'{folder_id}' in parents and trashed = false"}
            ).GetList()

            return [file for file in file_list]
        except Exception as e:
            logging.error(f"Failed to list files in folder '{folder_id}': {e}")
            raise

    def download_files(self, file: GoogleDriveFile, download_path: str):
        """
        Download all files from the file list to the specified download path.
        """
        try:
            if not os.path.exists(download_path):
                os.makedirs(download_path)
            file_title = file["title"]
            logging.info(f"Downloading: {file_title}")
            file.GetContentFile(os.path.join(download_path, file_title))
        except Exception as e:
            logging.error(f"Failed to download file '{file['title']}': {e}")
            raise

    def upload_file(
        self, file_path: str, folder_id: str, file_name: str = None
    ) -> GoogleDriveFile:
        """
        Upload a file to the specified folder.
        """
        try:
            if not file_name:
                file_name = os.path.basename(file_path)
            google_drive_file = self.drive.CreateFile(
                {"title": file_name, "parents": [{"id": folder_id}]}
            )
            google_drive_file.SetContentFile(file_path)
            google_drive_file.Upload()

            google_drive_file.InsertPermission(
                {"type": "anyone", "value": "anyone", "role": "reader"}
            )

            return google_drive_file
        except Exception as e:
            logging.error(f"Failed to upload file '{file_path}': {e}")
            raise
