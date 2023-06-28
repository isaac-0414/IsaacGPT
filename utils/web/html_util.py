from bs4 import BeautifulSoup
import re

def get_links_from_html_file(html: str):
    soup = BeautifulSoup(html, 'html5lib')
    links = []
    for anchor_tags in soup.find_all('a'):
        link = anchor_tags.get('href')
        description = anchor_tags.text
        links.append({"link": link, "description": description})
    return links
    
def get_body_from_html(html: str):
    soup = BeautifulSoup(html, 'html5lib')
    # get rid of all the script, i, and img tags
    for s in soup.select('script'):
        s.decompose()
    for i in soup.select('i'):
        i.decompose()
    for img in soup.select('img'):
        img.decompose()

    html_body_content = soup.body.text

    # formatting
    html_body_content = html_body_content.strip()
    html_body_content = re.sub('(\n )+', '\n', html_body_content)
    html_body_content = re.sub('( \n)+', '\n', html_body_content)
    html_body_content = re.sub('[\r\n]+', '\n', html_body_content)
    html_body_content = re.sub('[\t ]+', ' ', html_body_content)
    return html_body_content


def add_divider(soup, node, threshold):
    if isinstance(node, str):
        return
    tags = set()
    children_count = set()
    for child in node.children:
        if child == "\n":
            child.decompose()

        add_divider(  # pylint: disable=cell-var-from-loop
            child, threshold
        )
        tags.add(child.name)
        if hasattr(child, "contents"):
            children_count.add(len(child.contents))

    if (
        node.name
        not in {
            "ul",
            "ol",
            "table",
            "tbody",
            "thead",
            "tr",
            "td",
            "th",
        }
        and len(tags) == 1
        and len(children_count) == 1
        and len(node.contents) >= threshold
    ):
        for i in range(-len(node.contents) + 1, 0, 1):
            new_tag = soup.new_tag(
                "p"
            )  # pylint: disable=cell-var-from-loop
            new_tag.string = "______"
            node.insert(i, new_tag)