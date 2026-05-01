import pluggy
from model import PluginResult, PluginQuery, AddAllResult
from settings import APPLICATION_NAME
from typing import Generator, Tuple
import re
from playwright.sync_api import sync_playwright
from playwright.sync_api import expect
from playwright_recaptcha import recaptchav3
import random
import time

hookimpl = pluggy.HookimplMarker(APPLICATION_NAME + "-plugins")
PLUGIN_NAME = "AddAll"

@hookimpl
def extract(query: PluginQuery) -> Generator[PluginResult, None, None]:
    isbn = query.data.isbn
    url = "https://www.addall.com"
    
    # Open playwright and goto url
    with sync_playwright() as p:
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
            box = page.locator("button[type='submit'][class='newbtn']").bounding_box()
            
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

        print(page.content())
        
        title = page.locator("div").locator("div[class='ntitle']").inner_text()
        author = page.locator("div").locator("div[class='nauthor']").inner_text()[3:]
        divs_locator = page.locator("div").locator("div[class='nrecordx']")
        divs = divs_locator.all()
        for div in divs:
            div_buyat = div.locator("div[class='buyat']")

            div_used = div_buyat.locator("div[class='used']")
            try:
                expect(div_used).to_have_count(1)
                continue
            except Exception as e:
                pass

            anchor_locator = div_buyat.locator("a")
            affiliate = anchor_locator.inner_text()
            url = f'{url}{anchor_locator.get_attribute("href")}'

            div_total = div.locator("div[class='total']")
            anchor_locator = div_total.locator("a")
            price = anchor_locator.inner_text()
            result = PluginResult[Tuple[str, str, str, float, str, str]](plugin_name="", plugin_data=(isbn, title, author, price, affiliate, url))
            yield result

        browser.close()
        
@hookimpl
def transform(data: PluginResult) -> Generator[PluginResult, None, None]:
    yield data

@hookimpl
def load(data: PluginResult) -> Generator[PluginResult, None, None]:
    print(f"data={data}")
    result = AddAllResult(isbn=data.plugin_data[0], title=data.plugin_data[1], author=data.plugin_data[2], price=data.plugin_data[3], url_text=data.plugin_data[4], url=data.plugin_data[5])
    yield PluginResult[AddAllResult](plugin_name=PLUGIN_NAME, plugin_data=result)
