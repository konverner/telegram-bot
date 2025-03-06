import base64
import io
import os

from PIL import Image


def image_to_base64(image: Image) -> str:
    """
    Converts a PIL Image to a base64 string.

    Args:
        image (Image): The image to convert.

    Returns:
        str: Base64 encoded string of the image.
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")  # or any other format
    return base64.b64encode(buffered.getvalue()).decode()


def download_file_on_disk(bot, file_id: str, file_path: str) -> None:
    """
    Downloads a file from Telegram servers and saves it to the specified path.

    Args:
        bot: The Telegram bot instance.
        file_id: The unique identifier for the file to be downloaded.
        file_path: The local path where the downloaded file will be saved.
    """
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, "wb") as file:
        file.write(downloaded_file)


def download_file_in_memory(bot, file_id: str) -> io.BytesIO:
    """
    Downloads a file from Telegram servers and parses it without saving it locally.

    Args:
        bot: The Telegram bot instance.
        file_id: The unique identifier for the file to be downloaded.

    Returns:
        io.BytesIO: The file object containing the downloaded file.
    """
    file_info = bot.get_file(file_id)
    downloaded_file: bytes = bot.download_file(file_info.file_path)

    # Convert bytes to a BytesIO object
    file_object = io.BytesIO(downloaded_file)

    return file_object


def extract_latex_block(text: str) -> str:
    """
    Extracts the LaTeX block ```latex ... ``` from the given text.
    """
    start = text.find("```latex")
    if start == -1:
        return ""
    end = text.find("```", start + 8)
    if end == -1:
        return ""
    return text[start + 8 : end].strip()
