import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from html2text import html2text
import copy
from utils.split_text import split_text_by_char_len
from utils.process_md import remove_links, remove_multi_line_breaks, format_md
from utils.gpt import gpt4_chat

logger = logging.getLogger(__name__)

def _html2md(soup: BeautifulSoup) -> str:
    simple_tree = soup.prettify() 
    markdown = html2text(str(simple_tree))
    markdown = remove_links(markdown)
    markdown = format_md(markdown)
    markdown = remove_multi_line_breaks(markdown)
    return markdown


def _have_at_least_one_same_class(classes1: List, classes2: List) -> bool:
    if classes1 == classes2:
        return True
    for class1 in classes1:
        for class2 in classes2:
            if class1 == class2:
                return True
    return False



class HTMLPreprocessor:
    """
    preprocess HTML to markdown and "lists".
    Clean the webpage(remove useless elements that will lower performance of LLM)
    Also split the webpage to chunks.
    """
    
    def __init__(
        self,
        html: str,
        base_url: Optional[str]=None
    ):
        self.soup: BeautifulSoup = None
        self.html_source: str = html
        self.base_url = base_url
        self.complete_markdown: str = None
        self.title: str = None
        self.header = {"source": "", "markdown": ""}
        self.footer = {"source": "", "markdown": ""}
        self.sidebars: List[Dict[str, str]] = []
        self.hyperlinks: List[str] = []
        self.lists: List[BeautifulSoup] = []
        self.loaded = False
        self.preprocess()
    

    def preprocess(self) -> None:
        """
        Called when the instance created, preprocess the HTML to everything we need
        """
        self.soup = BeautifulSoup(
            "".join(s.strip() for s in self.html_source.split("\n")),
            "html.parser",
        )

        # remove scripts and styles
        for s in self.soup.select("script"):
            s.extract()
        for s in self.soup.select("style"):
            s.extract()

        title = self.soup.find("title").string
        self.title = title if title else None

        # remove head if there is one
        head = self.soup.find("head")
        if head:
            head.extract()

        self.find_hyperlinks()
        self.extract_hidden() # remove all the hidden elements if has style property or hidden property
        self.extract_header_footer() # remove headers and footers
        self.extract_sidebar() # remove sidebar (if can)
        self.get_lists(5) # get all the "lists" (elements with similar structure)

        self.complete_markdown = _html2md(self.soup.body)

        self.loaded = True


    def find_hyperlinks(self) -> list[str]:
        """
        Find all the hyperlinks on this page, result will be both returned and stored in self.hyperlinks
        """
        if not self.base_url:
            return
        links = self.soup.find_all('a', href=True)
        link_tuples = []
        for link in links:
            if link["href"].startswith("http"):
                link_tuples.append((link.text, link["href"]))
            elif not link["href"].startswith("/"):
                continue
            else:
                link_tuples.append((link.text, self.base_url + link["href"][1:]))

        def format_hyperlinks(link_tuples: list[tuple[str, str]]) -> list[str]:
            return [f"{link_text} ({link_url})" for link_text, link_url in link_tuples]
        
        self.hyperlinks = format_hyperlinks(link_tuples)
        return self.hyperlinks
    

    def extract_header_footer(self) -> None:
        """
        Try to find header and footer, store them and remove them in the markdown doc
        """
        header = self.soup.find('header')
        if not header:
            header = self.soup.find(class_='header')
            if not header:
                header = self.soup.find(id='header')
        if header:
            self.header["source"] = str(header)         
            self.header["markdown"] = _html2md(header)
            header.extract()
        footer = self.soup.find('footer')
        if not footer:
            footer = self.soup.find(class_='footer')
            if not footer:
                footer = self.soup.find(id='footer')
        if footer:
            self.footer["source"] = str(footer)
            self.footer["markdown"] = _html2md(footer)
            footer.extract()
    

    def extract_sidebar(self) -> None:
        """
        Try to remove sidebar on the page, often not work
        """
        def extract_sidebar_helper(node):
            if (node.has_attr('class') and 'sidebar' in node['class']) or (node.has_attr('id') and 'sidebar' == node['id']): 
                md = _html2md(node)
                self.sidebars.append({"source": str(node), "markdown": md})
                node.extract()
                return
            for child in node.find_all(recursive=False):
                extract_sidebar_helper(child)
        extract_sidebar_helper(self.soup.body)


    def extract_hidden(self) -> None:
        """
        Remove all the invisible elements on the page
        """
        def extract_hidden_helper(node):
            if isinstance(node, str) or len(node.find_all(recursive=False)) == 0:
                return
            if node.hidden:
                node.extract()
                return
            style = node.get('style')
            if style:
                if ('display' in style and 'none' in style) or ('visibility' in style and node.has_attr('hidden')):
                    node.extract()
                    return
            for child in node.find_all(recursive=False):
                extract_hidden_helper(child)
        extract_hidden_helper(self.soup.body)


    def get_lists(self, threshold=5) -> None:
        """
        Get all the "lists" in the webpage, go to my research report for more information on "lists"

        Parameters:
        threshold: minimum number of elements a list need to have.
        """
        # this helper function is for pre-order traversal
        def get_lists_helper(node: BeautifulSoup, threshold: int) -> None:
            if isinstance(node, str) or len(node.find_all(recursive=False)) == 0:
                return

            # remove all the line breaks
            for child in node.children:
                if child == "\n":
                    child.decompose()

            # do pre-order traversal
            for child in node.find_all(recursive=False):
                get_lists_helper(  # pylint: disable=cell-var-from-loop
                    child, threshold
                )

            # find the number of consecutive children have the exact same structure
            subtree = None
            max_len_children_same_structure = 1
            curr_len_children_same_structure = 1
            for child in node.find_all(recursive=False):
                subtree_rooted_at_child = [tag.name for tag in child.find_all(recursive=True)]
                if subtree is None:
                    subtree = subtree_rooted_at_child
                else:
                    if (subtree == subtree_rooted_at_child) and not (isinstance(child, str) or len(child.find_all(recursive=False)) == 0):
                        curr_len_children_same_structure += 1
                    else:
                        if curr_len_children_same_structure > max_len_children_same_structure:
                            max_len_children_same_structure = curr_len_children_same_structure
                        subtree = subtree_rooted_at_child if not (isinstance(child, str) or len(child.find_all(recursive=False)) == 0) else None
                        curr_len_children_same_structure = 1
            
            if curr_len_children_same_structure > max_len_children_same_structure:
                max_len_children_same_structure = curr_len_children_same_structure
                        
            
            # find the number of consecutive children have the same tag and class
            max_len_children_same_tag_class = 1
            curr_len_children_same_tag_class = 1
            tag: str = None
            class_: List[str] = None
            for child in node.find_all(recursive=False):
                if tag is None or class_ is None:
                    if tag is None:
                        tag = child.name
                    if class_ is None:
                        class_ = child['class'] if child.has_attr('class') else []
                elif _have_at_least_one_same_class(child['class'] if child.has_attr('class') else [], class_) and child.name == tag and not (isinstance(child, str) or len(child.find_all(recursive=False)) == 0):
                    curr_len_children_same_tag_class += 1
                else:
                    if (curr_len_children_same_tag_class > max_len_children_same_tag_class):
                        max_len_children_same_tag_class = curr_len_children_same_tag_class
                    tag = child.name if not (isinstance(child, str) or len(child.find_all(recursive=False)) == 0) else None
                    class_ = (child['class'] if child.has_attr('class') else []) if not (isinstance(child, str) or len(child.find_all(recursive=False)) == 0) else None
                    curr_len_children_same_tag_class = 1
            
            if curr_len_children_same_tag_class > max_len_children_same_tag_class:
                max_len_children_same_tag_class = curr_len_children_same_tag_class
            

            # find the number of consecutive children that forms some pattern, e.g. h2, div, p, h2, div, p, h2...
            first_node = None
            first_component: List = None
            component = list()
            components = list()
            components_same_tag = True
            
            for child in node.find_all(recursive=False):
                if first_node is None:
                    component.append(child)
                    first_node = child
                    continue
                if (child.name != first_node.name):
                    component.append(child)
                else:
                    if first_component is None:
                        first_component = component
                    else:
                        if len(first_component) != len(component):
                            components_same_tag = False
                            break
                        for i in range(len(first_component)):
                            if (first_component[i].name != component[i].name):
                                components_same_tag = False
                                break
                    if len(component) == 1:
                        components_same_tag = False
                        break

                    components.append(component)
                    component = [child]
            
            if first_component is not None:
                if len(first_component) != len(component):
                    components_same_tag = False
                else:
                    for i in range(len(first_component)):
                        if (first_component[i].name != component[i].name):
                            components_same_tag = False
                if len(component) == 1:
                    components_same_tag = False
                
                if components_same_tag:
                    components.append(component)


            if (components_same_tag and len(components) >= threshold):  
                # this is for ease of later work
                # e.g. if the pattern is h2, div, p, h2, div, p, h2, div, p
                # I am creating a parent div for each h2, div, p
                new_root = self.soup.new_tag("div")
                for component in components:
                    new_div = self.soup.new_tag("div")
                    for node in component:
                        new_div.append(copy.copy(node))
                    new_root.append(new_div)
                self.lists.append(new_root)
                return

            elif (max_len_children_same_structure >= threshold):
                self.lists.append(node)
                return
            
            elif (max_len_children_same_tag_class >= threshold):
                self.lists.append(node)
                return
            
        get_lists_helper(self.soup.body, threshold)

    def build_lists_split(self, window_size: int=6000) -> List[str]:
        """
        Create split of lists, each two element would be separated by a  "______"

        Parameters:
        window_size (int): the length of each chunk of split in number of characters
        
        Returns:
        List[str]: the split
        """
        if not self.loaded:
            raise Exception('please use the load() function before building split of lists')
        split: List[str] = []
        tmp = ""
        for list in self.lists:
            for child in list.children:
                text = _html2md(child)
                if len(text) > window_size:
                    break
                if len(tmp + text) > window_size:
                    split.append(tmp)
                    tmp = text
                else:
                    if tmp == "":
                        tmp = text
                    else:
                        tmp += "\n______\n" + text
            if len(tmp) > 0:
                split.append(tmp)
        # there might be duplicates, remove all the duplicates
        i = 0
        while i < len(split):
            j = 0
            while j < len(split):
                if j != i:
                    # if one element is in another element, remove it
                    if split[i] in split[j]:
                        split.pop(i)
                        i -= 1
                        break
                j += 1
            i += 1
        return split
    
    # window size here is number of characters
    def build_split(self, window_size: int=6000, stride: int=6000) -> List[str]:
        """
        Split the webpage based on number of characters. See more information on the research report.
        You can also set the overlap by the "stride"
        argument.

        Parameters:
        window_size (int): the length of each chunk of split in number of characters
        stride (int or None): e.g. if stride=3000, the distance between the starts of two chunks are 3000 characters.

        Returns:
        List[str]: the split
        """
        if len(self.complete_markdown) < window_size:
            return [self.complete_markdown]
        def build_split_helper(node, window_size) -> List[str]:
            # base case
            if len(node.find_all(recursive=False)) == 0:        
                md = _html2md(node)
                if len(md) > window_size:
                    return split_text_by_char_len(md, window_size=window_size, stride=stride)
                else:
                    return [md]
            
            split_list = list()
            # do a post order traversal
            for child in node.find_all(recursive=False):
                split_list += build_split_helper(child, window_size)
                    
            md = _html2md(node)
            if len(md) > window_size:
                return split_list
            else:
                return [md]
        split = build_split_helper(self.soup.body, window_size)

        new_split: List[str] = [""]
        can_add: List[bool] = [True]
        stride_tmp = ""
        for chunk in split:
            for i in range(len(new_split)):
                if can_add[i] and len(new_split[i] + chunk) > window_size:
                    can_add[i] = False
                if can_add[i] and len(new_split[i] + chunk) <= window_size:
                    new_split[i] += chunk
            if len(stride_tmp + chunk) <= stride:
                stride_tmp += chunk
            else:
                new_split.append(chunk)
                can_add.append(True)
                stride_tmp = chunk
        
        return new_split
    
    def summarize(self) -> str:
        """
        Summarize the webpage in map-reduce style
        """
        split = self.build_split(window_size=20000)
        if len(split) == 1:
            system_msg = f'This is content of the webpage "{self.title}":\n\n{self.complete_markdown}'
            user_msg = 'Provide a detailed summary of this webpage.'
            return gpt4_chat(system_msg, user_msg)
        else:
            part_summaries = []
            for chunk in split:
                system_msg = f'This is part of content of the webpage "{self.title}":\n\n{chunk}'
                user_msg = 'Provide a detailed summary of this part of webpage.'
                part_summary = gpt4_chat(system_msg, user_msg)
                part_summaries.append(part_summary)
            summaries_str = "\n______\n".join(part_summaries)
            system_msg = f'Here are summaries of each part of the webpage "{self.title}":\n\n{summaries_str}'
            user_msg = 'Provide a detailed summary of the entire webpage.'
            return gpt4_chat(system_msg, user_msg)
         
    
    def save_source(self, file_path) -> None:
        """
        Save HTML source code
        """
        if not self.html_source:
            raise ValueError('No HTML source currently, please use load() function first')
        with open(file_path, 'w') as f:
            f.write(self.html_source)
    
    def save_markdown(self, file_path) -> None:
        """
        Save processed markdown
        """
        if not self.complete_markdown:
            raise ValueError('No markdown currently, please use load() function first')
        with open(file_path, 'w') as f:
            f.write(self.complete_markdown)