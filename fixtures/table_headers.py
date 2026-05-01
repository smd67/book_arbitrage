import pluggy
from typing import Dict, List, Any
from settings import APPLICATION_NAME

hookimpl = pluggy.HookimplMarker(APPLICATION_NAME + "-fixtures")

@hookimpl
def get_table_headers() -> List[Dict[Any, Any]]:

    headers = [
        {'title': 'Retailer', 'align': 'start', 'value': 'retailer', 'sortable': True, 'class': 'blue lighten-5'},
        {'title': 'ISBN', 'value': 'isbn' , 'sortable': True},
        {'title': 'Title', 'value': 'title' , 'sortable': True},
        {'title': 'Author', 'value': 'author' , 'sortable': True},
        {'title': 'Price', 'value': 'price' , 'sortable': True},
        {'title': 'URL', 'value': 'url' , 'sortable': True},
        {'text': 'Actions', 'value': 'actions', 'sortable': False }
    ]
    return headers