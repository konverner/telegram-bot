import logging
import re
from pathlib import Path

import yt_dlp

logger = logging.getLogger(__name__)

# Define a default download directory (consider making this configurable)
DEFAULT_DOWNLOAD_PATH = Path("./downloads")
DEFAULT_DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)


class DownloadError(Exception):
    """Custom exception for download errors."""

    pass


class YtDlpClient:
    def __init__(
        self,
        download_path: Path = DEFAULT_DOWNLOAD_PATH,
        cookie_path: Path = Path("./src/app/plugins/yt_dlp/resources/cookies.txt"),
        logger: logging.Logger | None = None,
    ):
        self.download_path = download_path
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.cookie_path = cookie_path if cookie_path else None
        self.logger = (logger or logging.getLogger(__name__)).getChild("YtDlpClient")

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Removes or replaces characters invalid for filenames."""
        sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        return sanitized if sanitized else "downloaded_file"

    def download_youtube_content(self, url: str, download_type: str) -> Path:
        """
        Downloads YouTube video or audio using yt-dlp.

        Args:
            url: The URL of the YouTube video.
            download_type: "video" or "audio".

        Returns:
            The Path object of the downloaded file.

        Raises:
            ValueError: If download_type is invalid.
            DownloadError: If yt-dlp encounters an error or the file isn't found.
        """
        logger = self.logger
        output_path = self.download_path
        logger.info(f"Attempting to download {download_type} from {url} to {output_path}")

        video_id = None
        video_title = None
        sanitized_title = None

        # --- 1. Extract Info First to get a stable ID and Title ---
        try:
            logger.debug(f"Extracting info for {url}")
            ydl_info_opts = {
                "quiet": True,
                "noplaylist": True,
                "logger": logger.getChild("yt_dlp_info"),
                "logtostderr": False,
            }
            if self.cookie_path and self.cookie_path.exists():
                ydl_info_opts["cookiefile"] = str(self.cookie_path)

            with yt_dlp.YoutubeDL(ydl_info_opts) as ydl_info:
                info_dict = ydl_info.extract_info(url, download=False)
                video_id = info_dict.get("id")
                video_title = info_dict.get("title")
                if not video_id:
                    logger.error(f"Could not extract video ID from info_dict for {url}. Info: {info_dict}")
                    raise DownloadError("Could not extract video ID.")
                if not video_title:
                    logger.warning(f"Could not extract video title for {url} (ID: {video_id}). Using ID as fallback.")
                    video_title = video_id
                sanitized_title = self.sanitize_filename(video_title)
                logger.debug(f"Extracted video ID: {video_id}, Title: '{video_title}', Sanitized: '{sanitized_title}'")
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"yt-dlp error during info extraction for {url}: {e}", exc_info=True)
            raise DownloadError(f"Failed to extract video info: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during info extraction for {url}: {e}", exc_info=True)
            raise DownloadError(f"An unexpected error occurred during info extraction: {e}")

        # --- 2. Prepare Download Options ---
        output_tmpl = str(output_path / f"{sanitized_title}.%(ext)s")
        final_expected_ext = ""

        def hook(d):
            if d["status"] == "finished":
                file_info = d.get("filename", "N/A")
                logger.info(f"yt-dlp hook: status 'finished'. File hint: {file_info}")
            elif d["status"] == "error":
                logger.error("yt-dlp hook: status 'error' reported.")

        ydl_opts = {
            "outtmpl": output_tmpl,
            "quiet": True,
            "noplaylist": True,
            "progress_hooks": [hook],
            "noprogress": True,
            "logtostderr": False,
            "logger": logger.getChild("yt_dlp_download"),
        }
        if self.cookie_path and self.cookie_path.exists():
            ydl_opts["cookiefile"] = str(self.cookie_path)

        if download_type == "video":
            ydl_opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best"
            ydl_opts["merge_output_format"] = "mp4"
            final_expected_ext = ".mp4"
        elif download_type == "audio":
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["extract_audio"] = True
            ydl_opts["audio_format"] = "mp3"
            ydl_opts["audio_quality"] = 0
            final_expected_ext = ".mp3"
        else:
            logger.error(f"Invalid download type specified: {download_type}")
            raise ValueError("Invalid download type. Choose 'video' or 'audio'.")

        # --- 3. Perform Download ---
        try:
            logger.info(f"Starting download process for '{sanitized_title}' (ID: {video_id}) with options: {ydl_opts}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.info(f"yt-dlp download process finished for '{sanitized_title}' (ID: {video_id}).")
        except yt_dlp.utils.DownloadError as e:
            logger.error(
                f"yt-dlp download error for {url} ('{sanitized_title}', ID: {video_id}): {e}",
                exc_info=True,
            )
            raise DownloadError(f"Failed to download: {e}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during download/processing for {url} ('{sanitized_title}', ID: {video_id}): {e}",
                exc_info=True,
            )
            raise DownloadError(f"An unexpected error occurred during download: {e}")

        # --- 4. Locate Final File ---
        expected_final_path = output_path / f"{sanitized_title}{final_expected_ext}"
        logger.debug(f"Checking for expected final file: {expected_final_path}")

        if expected_final_path.exists():
            logger.info(f"Successfully downloaded. Final file found at expected path: {expected_final_path}")
            return expected_final_path
        else:
            glob_pattern = "".join(["[" + c + "]" if c in "[]*?" else c for c in sanitized_title]) + ".*"
            logger.warning(
                f"Expected file {expected_final_path} not found. Scanning {output_path} for files matching pattern '{glob_pattern}'..."
            )
            found_files = list(output_path.glob(glob_pattern))

            if not found_files:
                logger.error(
                    f"Download process completed but no output file found for '{sanitized_title}' (ID: {video_id}) in {output_path}."
                )
                raise DownloadError(
                    f"Could not locate the final downloaded file for '{sanitized_title}' (ID: {video_id})."
                )

            potential_file = None
            for f in found_files:
                if f.suffix.lower() == final_expected_ext.lower():
                    potential_file = f
                    logger.info(f"Found file matching expected extension: {potential_file}")
                    break

            if potential_file:
                return potential_file
            else:
                first_found = found_files[0]
                logger.warning(
                    f"File with expected extension {final_expected_ext} not found for title '{sanitized_title}'. "
                    f"Returning first matching file found: {first_found}"
                )
                return first_found
