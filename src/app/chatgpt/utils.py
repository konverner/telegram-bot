import io


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
