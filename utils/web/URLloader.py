import os
import logging
from typing import List, Optional
from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from html2text import html2text
from .html_util import add_divider

os.environ["LANGCHAIN_HANDLER"] = "langchain"
logger = logging.getLogger(__name__)


class URLLoader(BaseLoader):
    """Loader that uses Playwright to load the page html and use readability.js
    and html2text library to sanitize and convert the raw html to markdown.

    Attributes:
        urls (List[str]): List of URLs to load.
        continue_on_failure (bool): If True, continue loading other URLs on failure.
        headless (bool): If True, the browser will run in headless mode.

    Note: this loader is converted from the original PlaywrightURLLoader
    """

    def __init__(
        self,
        urls: List[str],
        continue_on_failure: bool = True,
        headless: bool = True,
        remove_selectors: Optional[List[str]] = None,
    ):
        """Load a list of URLs using Playwright and unstructured."""
        self.urls = urls
        self.continue_on_failure = continue_on_failure
        self.headless = headless
        self.remove_selectors = remove_selectors

    def load(self) -> List[Document]:
        """Load the specified URLs using Playwright and create Document instances.

        Returns:
            List[Document]: A list of Document instances with loaded content.
        """

        docs: List[Document] = list()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            for url in self.urls:
                try:
                    page = browser.new_page()
                    page.goto(url, wait_until="domcontentloaded")

                    for selector in self.remove_selectors or []:
                        elements = page.locator(selector).all()
                        for element in elements:
                            if element.is_visible():
                                element.evaluate("element => element.remove()")

                    page_source = page.content()
                    # readabilipy is used to remove scripts and styles
                    # simple_tree = simple_tree_from_html_string(page_source)

                    soup = BeautifulSoup(
                        "".join(s.strip() for s in page_source.split("\n")),
                        "html.parser",
                    )

                    for s in soup.select("script"):
                        s.extract()
                    for s in soup.select("style"):
                        s.extract()

                    add_divider(soup, soup.body, 3)
                    simple_tree = soup.prettify()
                    # html2text is used to convert html to markdown
                    text = html2text(str(simple_tree))
                    metadata = {"source": url}
                    docs.append(Document(page_content=text, metadata=metadata))
                except Exception as err:  # pylint: disable=broad-except
                    if self.continue_on_failure:
                        logger.error(
                            "Error fetching or processing %s, exception: %s", url, err
                        )
                    else:
                        raise err
            browser.close()
        return docs