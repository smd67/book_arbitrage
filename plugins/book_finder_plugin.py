import pluggy
from model import PluginResult, PluginQuery, BookFinderResult
from settings import APPLICATION_NAME
from typing import Generator, Tuple
import re
from playwright.sync_api import sync_playwright
from playwright.sync_api import expect

hookimpl = pluggy.HookimplMarker(APPLICATION_NAME + "-plugins")
PLUGIN_NAME = "BookFinder"

@hookimpl
def extract(query: PluginQuery) -> Generator[PluginResult, None, None]:
    isbn = query.data.isbn
    url = "https://www.bookfinder.com/isbn/{isbn}/?author=&binding=ANY&condition=ANY&currency=USD&destination=US&firstEdition=false&isbn=9780679760849&keywords=&language=EN&maxPrice=&minPrice=&noIsbn=false&noPrintOnDemand=false&publicationMaxYear=&publicationMinYear=&publisher=&bunchKey=&signed=false&title=&viewAll=false&mode=BASIC"
    
    # Open playwright and goto url
    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
        page = browser.new_page()


        try:
            page.goto(url, timeout=60000)
        except Exception as e:
            print(f"Error: unexpected exception e={e}")
        
        page.locator("input[id='keywords']").first.fill(isbn)
        submit_button = page.locator("button[type='submit'][data-test-id='book-search-button-desktop']")
        submit_button.click(force=True)

        page.wait_for_load_state("networkidle")        
        
        divs_locator = page.locator("div").locator("div[data-csa-c-type='item']")
        divs = divs_locator.all()
        for div in divs:
            # Get text, click, or evaluate each div
            clean_text = div.inner_text().replace("\n", " ")
            if "Condition: New" not in clean_text:
                continue

            pattern = r"(\d+)[.][ ]+Edition:[ ]+([^,]+)[,][ ]+([^ ]+)[ ].*Condition: New[ ]+[$](\d+[.]\d{2})[ ]+From:[ ]+(.*)"

            title = div.get_attribute('data-csa-c-title')
            author = div.get_attribute('data-csa-c-authors')
            affiliate = div.get_attribute('data-csa-c-affiliate')
            links = div.locator("a").all()

            # Extract href from each
            urls = [link.get_attribute("href") for link in links]
            url = urls[0]

            price = 0.0
            match = re.search(pattern, clean_text)
            if match:
                price = float(match.group(4))
                result = PluginResult[Tuple[str, str, str, float, str, str]](plugin_name="", plugin_data=(query.data.isbn, title, author, price, affiliate, url))
                yield result
        browser.close()

@hookimpl
def transform(data: PluginResult) -> Generator[PluginResult, None, None]:
    yield data

@hookimpl
def load(data: PluginResult) -> Generator[PluginResult, None, None]:
    result = BookFinderResult(isbn=data.plugin_data[0], title=data.plugin_data[1], author=data.plugin_data[2], price=data.plugin_data[3], url_text=data.plugin_data[4], url=data.plugin_data[5])
    yield PluginResult[BookFinderResult](plugin_name=PLUGIN_NAME, plugin_data=result)
