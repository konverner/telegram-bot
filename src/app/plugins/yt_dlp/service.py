import logging
import os
from pathlib import Path
import re
import yt_dlp

logger = logging.getLogger(__name__)

# Define a default download directory (consider making this configurable)
DEFAULT_DOWNLOAD_PATH = Path("./downloads")
DEFAULT_DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)


class DownloadError(Exception):
    """Custom exception for download errors."""

    pass


def sanitize_filename(filename: str) -> str:
    """Removes or replaces characters invalid for filenames."""
    # Remove characters that are definitely invalid on most systems
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    # Replace colons used in timecodes etc. with something else if desired, or remove
    # sanitized = sanitized.replace(":", "-")
    # Replace excessive whitespace
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    # Limit length if necessary (optional)
    # max_len = 200
    # if len(sanitized) > max_len:
    #     sanitized = sanitized[:max_len].rsplit(' ', 1)[0] # Truncate at last space
    return sanitized if sanitized else "downloaded_file"  # Ensure filename is not empty


def download_youtube_content(
    url: str, download_type: str, output_path: Path = DEFAULT_DOWNLOAD_PATH
) -> Path:
    """
    Downloads YouTube video or audio using yt-dlp.

    Args:
        url: The URL of the YouTube video.
        download_type: "video" or "audio".
        output_path: The directory to save the downloaded file.

    Returns:
        The Path object of the downloaded file.

    Raises:
        ValueError: If download_type is invalid.
        DownloadError: If yt-dlp encounters an error or the file isn't found.
    """
    logger.info(f"Attempting to download {download_type} from {url} to {output_path}")

    video_id = None
    video_title = None
    sanitized_title = None
    # --- 1. Extract Info First to get a stable ID and Title ---
    try:
        logger.debug(f"Extracting info for {url}")
        # Use separate YDL instance for info extraction
        ydl_info_opts = {
            "quiet": True,
            "noplaylist": True,
            "logger": logger.getChild("yt_dlp_info"),
            "logtostderr": False,
            "cookiefile": "./src/app/yt_dlp/resources/cookies.txt",  # Update with the actual path to your cookies file
        }
        with yt_dlp.YoutubeDL(ydl_info_opts) as ydl_info:
            info_dict = ydl_info.extract_info(url, download=False)
            video_id = info_dict.get("id")
            video_title = info_dict.get("title")
            if not video_id:
                logger.error(
                    f"Could not extract video ID from info_dict for {url}. Info: {info_dict}"
                )
                raise DownloadError("Could not extract video ID.")
            if not video_title:
                logger.warning(
                    f"Could not extract video title for {url} (ID: {video_id}). Using ID as fallback."
                )
                video_title = video_id  # Fallback to ID if title is missing
            sanitized_title = sanitize_filename(video_title)
            logger.debug(
                f"Extracted video ID: {video_id}, Title: '{video_title}', Sanitized: '{sanitized_title}'"
            )
    except yt_dlp.utils.DownloadError as e:
        logger.error(
            f"yt-dlp error during info extraction for {url}: {e}", exc_info=True
        )
        raise DownloadError(f"Failed to extract video info: {e}")
    except Exception as e:
        logger.error(
            f"Unexpected error during info extraction for {url}: {e}", exc_info=True
        )
        raise DownloadError(f"An unexpected error occurred during info extraction: {e}")

    # --- 2. Prepare Download Options ---
    # Use the sanitized title for the output template filename part
    # yt-dlp will add the correct extension based on format/postprocessing
    output_tmpl = str(output_path / f"{sanitized_title}.%(ext)s")
    final_expected_ext = ""

    # Simplified progress hook for logging completion/errors
    def hook(d):
        if d["status"] == "finished":
            # 'filename' here might be temporary or post-processed path
            file_info = d.get("filename", "N/A")
            logger.info(f"yt-dlp hook: status 'finished'. File hint: {file_info}")
        elif d["status"] == "error":
            logger.error("yt-dlp hook: status 'error' reported.")
        # No need to access d['filename'] here to determine final path

    ydl_opts = {
        "outtmpl": output_tmpl,  # Use the template with the sanitized title
        "quiet": True,
        "noplaylist": True,
        "progress_hooks": [hook],
        # Removed postprocessor_hooks to simplify, rely on finding file later
        "noprogress": True,
        "logtostderr": False,
        "logger": logger.getChild("yt_dlp_download"),
    }
    cookie_path = Path("./src/app/plugins/yt_dlp/resources/cookies.txt")
    if cookie_path.exists():
        ydl_opts["cookiefile"] = str(cookie_path)

    if download_type == "video":
        # Prefer mp4, allow yt-dlp to choose best available if not directly mp4
        ydl_opts[
            "format"
        ] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best"
        ydl_opts[
            "merge_output_format"
        ] = "mp4"  # Request mp4 container if merging is needed
        final_expected_ext = ".mp4"
    elif download_type == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["extract_audio"] = True
        ydl_opts["audio_format"] = "mp3"
        ydl_opts["audio_quality"] = 0  # 0 is best for mp3
        final_expected_ext = ".mp3"
    else:
        logger.error(f"Invalid download type specified: {download_type}")
        raise ValueError("Invalid download type. Choose 'video' or 'audio'.")

    # --- 3. Perform Download ---
    try:
        logger.info(
            f"Starting download process for '{sanitized_title}' (ID: {video_id}) with options: {ydl_opts}"
        )
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # The download method doesn't return the final path directly in a reliable way
            # It relies on the options and hooks, which we found problematic.
            ydl.download([url])
        logger.info(
            f"yt-dlp download process finished for '{sanitized_title}' (ID: {video_id})."
        )

    except yt_dlp.utils.DownloadError as e:
        logger.error(
            f"yt-dlp download error for {url} ('{sanitized_title}', ID: {video_id}): {e}",
            exc_info=True,
        )
        raise DownloadError(f"Failed to download: {e}")
    except Exception as e:
        # Catching potential errors during download/postprocessing
        logger.error(
            f"An unexpected error occurred during download/processing for {url} ('{sanitized_title}', ID: {video_id}): {e}",
            exc_info=True,
        )
        raise DownloadError(f"An unexpected error occurred during download: {e}")

    # --- 4. Locate Final File ---
    # Construct the most likely final path based on sanitized title and requested format
    expected_final_path = output_path / f"{sanitized_title}{final_expected_ext}"
    logger.debug(f"Checking for expected final file: {expected_final_path}")

    if expected_final_path.exists():
        logger.info(
            f"Successfully downloaded. Final file found at expected path: {expected_final_path}"
        )
        return expected_final_path
    else:
        # Fallback: Scan the directory for files matching the sanitized title pattern.
        # This handles cases where the final extension might differ from the requested one
        # (e.g., if mp4 merge wasn't possible, it might be .mkv or .webm).
        # Escape regex special characters in the title before using glob
        glob_pattern = (
            "".join(["[" + c + "]" if c in "[]*?" else c for c in sanitized_title])
            + ".*"
        )
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

        # If multiple files match (e.g., .mp3 and .webp thumbnail), prioritize the expected one.
        potential_file = None
        for f in found_files:
            # Check if the file extension matches the expected one (case-insensitive)
            if f.suffix.lower() == final_expected_ext.lower():
                potential_file = f
                logger.info(f"Found file matching expected extension: {potential_file}")
                break  # Found the best match

        if potential_file:
            return potential_file
        else:
            # If no file with the *exact* expected extension is found, but *some* file exists,
            # return the first one found. This is a best-effort guess.
            first_found = found_files[0]
            logger.warning(
                f"File with expected extension {final_expected_ext} not found for title '{sanitized_title}'. "
                f"Returning first matching file found: {first_found}"
            )
            return first_found
