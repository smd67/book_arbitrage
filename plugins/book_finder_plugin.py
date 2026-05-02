"""
Plugin implementation that scrapes the BookFinder website at www.bookfinder.com.
"""

import os
import re
from typing import Generator, Tuple

import pluggy
from model import PluginQuery, PluginResult
from playwright.sync_api import sync_playwright
from pydantic import BaseModel

APPLICATION_NAME = os.getenv("APPLICATION_NAME")
APPLICATION_NAME = APPLICATION_NAME if APPLICATION_NAME else ""

hookimpl = pluggy.HookimplMarker(APPLICATION_NAME + "-plugins")
PLUGIN_NAME = "BookFinder"


class BookFinderResult(BaseModel):
    """
    Model for a result from BookFinder
    """
    isbn: str
    title: str
    author: str
    price: float
    url_text: str
    url: str


@hookimpl
def extract(query: PluginQuery) -> Generator[PluginResult, None, None]:
    """
    The extract method is used to pull data from various sources like REST
    APIs, web scraping, or databases. One source per plugin is a good rule
    of thumb.

    BookFinder does not use recaptcha, but the data is not formatted well by 
    so regular expressions are required.

    Parameters
    ----------
    query : PluginQuery
        A generic query sent from the frontend that includes any information
        required to extract the data.

    Yields
    ------
    Generator[PluginResult, None, None]
        A generator is returned so data can be streamed to the next step
        without having to gather it or wait for completion.
    """
    isbn = query.data["isbn"]
    url = (
        "https://www.bookfinder.com/isbn/{isbn}/"
        + "?author=&binding=ANY&condition=ANY&currency=USD"
        + "&destination=US&firstEdition=false&isbn={isbn}&keywords=&language"
        + "=EN&maxPrice=&minPrice=&noIsbn=false&noPrintOnDemand=false&"
        + "publicationMaxYear=&publicationMinYear=&publisher=&bunchKey=&"
        + "signed=false&title=&viewAll=false&mode=BASIC"
    )

    # Open playwright and goto url
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()

        try:
            page.goto(url, timeout=60000)
        except Exception as e:
            print(f"Error: unexpected exception e={e}")

        page.locator("input[id='keywords']").first.fill(isbn)
        submit_button = page.locator(
            "button[type='submit'][data-test-id='book-search-button-desktop']"
        )
        submit_button.click(force=True)

        page.wait_for_load_state("networkidle")

        divs_locator = page.locator("div").locator("div[data-csa-c-type='item']")
        divs = divs_locator.all()
        for div in divs:
            # Get text, click, or evaluate each div
            clean_text = div.inner_text().replace("\n", " ")
            if "Condition: New" not in clean_text:
                continue

            pattern = (
                r"(\d+)[.][ ]+Edition:[ ]+([^,]+)[,][ ]+([^ ]+)[ ].*"
                + r"Condition: New[ ]+[$](\d+[.]\d{2})[ ]+From:[ ]+(.*)"
            )

            title = div.get_attribute("data-csa-c-title")
            author = div.get_attribute("data-csa-c-authors")
            affiliate = div.get_attribute("data-csa-c-affiliate")
            links = div.locator("a").all()

            # Extract href from each
            urls = [link.get_attribute("href") for link in links]
            url = urls[0]

            price = 0.0
            match = re.search(pattern, clean_text)
            if match:
                price = float(match.group(4))
                result = PluginResult[Tuple[str, str, str, float, str, str]](
                    plugin_name="",
                    plugin_data=(isbn, title, author, price, affiliate, url),
                )
                yield result
        browser.close()


@hookimpl
def transform(data: PluginResult) -> Generator[PluginResult, None, None]:
    """
    The transform method is used to clean, map, and transform the extracted 
    data into a into a standardized format.

    In this case it is a pass through method.

    Parameters
    ----------
    data : PluginResult
        A generic result that contains one row of extractred data.

    Yields
    ------
    Generator[PluginResult, None, None]
        A generator is returned so data can be streamed to the next step
        without having to gather it or wait for completion.
    """
    yield data


@hookimpl
def load(data: PluginResult) -> Generator[PluginResult, None, None]:
    """
    The transformed, structured data is written into the destination system, 
    typically a data warehouse or data lake, but in our case it is used
    to marshall data into an internal storage.

    Parameters
    ----------
    data : PluginResult
        A generic result that contains one row of transformed data.

    Yields
    ------
    Generator[PluginResult, None, None]
        A generator is returned so data can be streamed to the next step
        without having to gather it or wait for completion.
    """
    result = BookFinderResult(
        isbn=data.plugin_data[0],
        title=data.plugin_data[1],
        author=data.plugin_data[2],
        price=data.plugin_data[3],
        url_text=data.plugin_data[4],
        url=data.plugin_data[5],
    )
    yield PluginResult[BookFinderResult](
        plugin_name=PLUGIN_NAME, plugin_data=result
    )
