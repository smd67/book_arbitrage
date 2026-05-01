
import pluggy
from typing import Dict
from model import PluginResult, AppResult
from typing import Dict, List
from pydantic import BaseModel
from settings import APPLICATION_NAME

hookimpl = pluggy.HookimplMarker(APPLICATION_NAME + "-fixtures")

class Result(BaseModel):
    retailer: str
    isbn: str
    title: str
    author: str
    price: float
    url_text: str
    url: str

@hookimpl
def merge_results(kv_store: Dict[str, PluginResult]) -> AppResult:
    results = []
    for k, v_list in kv_store.items():
        for v in v_list:
            result = Result(retailer=k, isbn=v.isbn, title=v.title, author=v.author, price=v.price, url_text=v.url_text, url=v.url)
            print(f"key={k}; result={result}")
            results.append(result)
    retval = AppResult[List](data=results)
    return retval
