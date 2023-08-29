import os
import logging
from typing import List, Optional
from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader
from playwright.sync_api import sync_playwright

os.environ["LANGCHAIN_HANDLER"] = "langchain"
logger = logging.getLogger(__name__)


class URLLoader(BaseLoader):
    def __init__(
        self,
        url: str = None,
        continue_on_failure: bool = True,
        headless: bool = True,
        remove_selectors: Optional[List[str]] = None
    ):
        """Load a list of URLs using Playwright and unstructured."""
        self.url = url

        self.continue_on_failure = continue_on_failure
        self.headless = headless
        self.remove_selectors = remove_selectors

        self.html = ""

    def load(self) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)                
            try:
                page = browser.new_page()
                page.goto(self.url, wait_until="domcontentloaded")

                for selector in self.remove_selectors or []:
                    elements = page.locator(selector).all()
                    for element in elements:
                        if element.is_visible():
                            element.evaluate("element => element.remove()")

                self.html = page.content()
            except Exception as err:  # pylint: disable=broad-except
                if self.continue_on_failure:
                    logger.error(
                        "Error fetching or processing %s, exception: %s", self.url, err
                    )
                else:
                    raise err
            browser.close()
        if self.html == '':
            raise Exception(f'Error when fetching the webpage {self.url}, please check the network condition or try again.')
        return self.html