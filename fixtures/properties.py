import pluggy
from typing import Dict, List, Any
from settings import APPLICATION_NAME

hookimpl = pluggy.HookimplMarker(APPLICATION_NAME + "-fixtures")

@hookimpl
def get_properties() -> Dict[Any, Any]:

    properties = {
        "title": "Book Arbitrage",
        "icon_height": 75,
        "icon_width": 75,
        "input_label": "ISBN",
        "title_style": "color: #CCA957; font-size: 24px",
        "table_style": "border: 1px solid #CCA957;",
        "input_color": "#CCA957",
        "table_header_color": '#E97451',
        "table_odd_color": '#ffffff',
        "table_even_color": '#E4D96F',
        "button_color": "#000000",
        "button_style": "background-color: #E4D96F !important;",
        "csv_file_name": "book_arbitrage.csv",
        "sort_by": [{ 'key': 'price', 'order': 'asc' }]
    }
    return properties