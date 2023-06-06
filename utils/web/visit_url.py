import requests

def fetch_HTML_content_from_url(url: str, save_file_path: str):
    try:
        response = requests.get(url)
        html_content = response.text

        # with open(save_file_path, 'w', encoding='utf-8') as outfile:
        #     outfile.write(html_content)

        return html_content
        
    except Exception as oops:
        print(f'Error fetching content from :{url}', oops)
