"""
Fixture implementation that returns the definition of each column of the 
table displayed by the frontend.
"""

# System imports
import os
from typing import Any, Dict, List

# 3rd Party imports
import pluggy

# Global variables
APPLICATION_NAME = os.getenv("APPLICATION_NAME", "")
hookimpl = pluggy.HookimplMarker(APPLICATION_NAME + "-fixtures")


@hookimpl
def get_table_headers() -> List[Dict[Any, Any]]:
    """
    This method returns a list of objects that describe a single column of
    data for the frontend.

    Returns
    -------
    List[Dict[Any, Any]]
        A list of column definitions
    """
    headers = [
        {
            "title": "Retailer",
            "align": "start",
            "value": "retailer",
            "sortable": True,
            "class": "blue lighten-5",
        },
        {"title": "ISBN", "value": "isbn", "sortable": True},
        {"title": "Title", "value": "title", "sortable": True},
        {"title": "Author", "value": "author", "sortable": True},
        {"title": "Price", "value": "price", "sortable": True},
        {"title": "URL", "value": "url", "sortable": True},
        {"text": "Actions", "value": "actions", "sortable": False},
    ]
    return headers
