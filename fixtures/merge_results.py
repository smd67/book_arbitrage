"""
Fixture implementation that merges the final results to send to the front
end.
"""

# System imports
import os
from typing import Dict, List

# 3rd Party imports
import pluggy
from model import AppResult, PluginResult
from pydantic import BaseModel

# Global variables
APPLICATION_NAME = os.getenv("APPLICATION_NAME", "")
hookimpl = pluggy.HookimplMarker(APPLICATION_NAME + "-fixtures")

# Pydantic model for merged results
class Result(BaseModel):
    """
    Model for returned data
    """
    retailer: str
    isbn: str
    title: str
    author: str
    price: float
    url_text: str
    url: str

@hookimpl
def merge_results(kv_store: Dict[str, PluginResult]) -> AppResult:
    """
    This method can be used to take the results from all of the plugins and 
    merge them together into a single coherent result.

    Parameters
    ----------
    kv_store : Dict[str, PluginResult]
        The in-memory store of results by plugin-name.

    Returns
    -------
    AppResult
        The final merged results.
    """
    results = []
    for k, v_list in kv_store.items():
        for v in v_list:
            result = Result(
                retailer=k,
                isbn=v.isbn,
                title=v.title,
                author=v.author,
                price=v.price,
                url_text=v.url_text,
                url=v.url,
            )
            print(f"key={k}; result={result}")
            results.append(result)
    retval = AppResult[List](data=results)
    return retval
