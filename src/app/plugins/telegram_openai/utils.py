import base64
import io

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
