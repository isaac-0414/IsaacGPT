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
