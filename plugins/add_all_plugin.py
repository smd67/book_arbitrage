"""
Plugin implementation that scrapes the AddAll website at www.addall.com.
"""
import os
import random
import time
from typing import Generator, Tuple

import pluggy
from model import PluginQuery, PluginResult
from playwright.sync_api import expect, sync_playwright
from playwright_recaptcha import recaptchav3
from pydantic import BaseModel

# Global variables
APPLICATION_NAME = os.getenv("APPLICATION_NAME", "")
PLUGIN_NAME = "AddAll"
hookimpl = pluggy.HookimplMarker(APPLICATION_NAME + "-plugins")

# Pydantic model declarations
class AddAllResult(BaseModel):
    """
    Model for a result from AddAll
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

    AddAll uses recaptcha so it is a little more complicated and takes longer.
    It requires the browser to be run non-headless requiring the use of the xvfb
    x-window server, use of the the recaptcha library to generate a token, 
    random pauses and non-centered clicks, plus retry logic.

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

    MAX_RETRIES = 15
    isbn = query.data["isbn"]
    url = "https://www.addall.com"
    is_success = False
    number_retries = 0

    # Open playwright and goto url
    with sync_playwright() as p:
        while not is_success and number_retries < MAX_RETRIES:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            try:
                with recaptchav3.SyncSolver(page) as solver:
                    page.goto(url, timeout=60000)
                    token = solver.solve_recaptcha()
                    print(f"Generated v3 Token: {token}")
            except Exception as e:
                print(f"v3 EXCEPTION!!!! - {e}. Sleeping")

            newform = page.locator("form[name='newform']")

            # 1. Locate the specific form (by ID, class, or text)
            isbn_select = newform.locator("select[name='type']")
            expect(isbn_select).to_have_count(1)
            time.sleep(random.uniform(2.0, 10.0))
            isbn_select.select_option(value="ISBN")

            search_input = newform.locator("input[id='query']")
            expect(search_input).to_have_count(1)
            search_input.type(isbn, delay=random.randint(50, 150))

            print("sleep prior after type")
            time.sleep(random.uniform(2.0, 10.0))
            with page.expect_navigation():
                # 1. Find bounding box
                box = page.locator(
                    "button[type='submit'][class='newbtn']"
                ).bounding_box()

                # 2. Calculate random point inside bounding box
                x = box["x"] + random.uniform(0, box["width"])
                y = box["y"] + random.uniform(0, box["height"])

                print("sleep prior to move")
                time.sleep(random.uniform(2.0, 10.0))

                # 3. Move mouse to that point
                page.mouse.move(x, y)

                print("sleep prior to click")
                # 4. Random wait
                time.sleep(random.uniform(2.0, 10.0))

                # 5. Click
                page.mouse.click(x, y)

            page.wait_for_load_state("load")

            try:
                title = page.locator("div").locator("div[class='ntitle']").inner_text()
                is_success = True
            except Exception as e:
                print(f"Retrying after unexpected exception e={e}")
                browser.close()
                number_retries += 1
        
        
        author = (
            page.locator("div").locator("div[class='nauthor']").inner_text()[3:]
        )
        divs_locator = page.locator("div").locator("div[class='nrecordx']")
        divs = divs_locator.all()
        for div in divs:
            div_buyat = div.locator("div[class='buyat']")

            div_used = div_buyat.locator("div[class='used']")
            try:
                expect(div_used).to_have_count(1)
                continue
            except Exception:
                pass

            anchor_locator = div_buyat.locator("a")
            affiliate = anchor_locator.inner_text()
            url = f'{url}{anchor_locator.get_attribute("href")}'

            div_total = div.locator("div[class='total']")
            anchor_locator = div_total.locator("a")
            price = anchor_locator.inner_text()
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
    print(f"data={data}")
    result = AddAllResult(
        isbn=data.plugin_data[0],
        title=data.plugin_data[1],
        author=data.plugin_data[2],
        price=data.plugin_data[3],
        url_text=data.plugin_data[4],
        url=data.plugin_data[5],
    )
    yield PluginResult[AddAllResult](plugin_name=PLUGIN_NAME, plugin_data=result)
