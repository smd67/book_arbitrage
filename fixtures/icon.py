"""
Fixture implementation that returns an icon image.
"""

# System imports
import base64
import os

# 3rd Party imports
import pluggy

# Global variables
APPLICATION_NAME = os.getenv("APPLICATION_NAME", "")
hookimpl = pluggy.HookimplMarker(APPLICATION_NAME + "-fixtures")


@hookimpl
def get_icon() -> str:
    """
    Returns an icon image used by the frontend.

    Returns
    -------
    str
        A base64 encoded string of the icon image.
    """
    assets_dir = os.getenv("ASSETS_DIR", "src/assets")
    icon_path = f"{assets_dir}/book-4986_64.png"

    # Open image file in 'rb' (read-binary) mode
    with open(icon_path, "rb") as image_file:
        # Read data and encode to Base64 bytes
        encoded_bytes = base64.b64encode(image_file.read())

        # Convert bytes to a UTF-8 string for use in HTML/JSON
        base64_string = encoded_bytes.decode("utf-8")

        data_uri = f"data:image/png;base64,{base64_string}"
    return data_uri
