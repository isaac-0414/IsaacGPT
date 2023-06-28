import torch
import bs4
from typing import List, Optional, Tuple, Union
from transformers import BartTokenizer


class Node:
    """
    Super class of DomNode and TextNode, represent any type of node in the Dom Tree
    """
    def __init__(self, tag: str, node_index: int, sib_index: int, parent_index: int, depth: int):
        self.tag = tag # HTML tag of the Node
        self.node_index = node_index # index of the node
        self.sib_index = sib_index # position of this node relative to its siblings
        self.parent_index = parent_index # Index of parent in the Dom tree
        self.depth = depth

class HTMLNode(Node):
    """
    This class represents an HTML node in a dom tree
    """
    def __init__(self, node_index: int, sib_index: int, tag: str, class_list: Optional[List[str]], id: Optional[str], children: Optional[Node], parent: Optional[Node], depth: int):
        super().__init__(tag, node_index, sib_index, parent.node_index, depth)
        self.class_list = class_list # class of the HTML element
        self.id = id # id of the HTML element
        self.children = children # children in the Dom tree
        self.parent = parent # parent in the Dom tree
    
    def add_child(self, child: Node):
        self.children.append(child)

class TextNode(Node):
    """
    This class represents a piece of text belongs to the Dom Tree
    """
    def __init__(self, node_index: int, sib_index: int, text: str, parent: HTMLNode, depth: int):
        super().__init__(parent.tag, node_index, sib_index, parent.node_index, depth)
        self.node_index = node_index # index of the node, used in positional encoding
        self.text = text
        self.parent = parent # parent in the Dom tree


class Token:
    """
    This class represents a token in the model, which is similar to a word in the input
    """
    def __init__(self, position: int, token: torch.Tensor, node: Node):
        self.position = position
        self.token = token
        self.node = node


class DomTree:
    """
    This class preprocess HTML into a tree structure to prepare for positional encoding and
    local self attention my model
    """
    def __init__(self, html: str):
        soup = bs4.BeautifulSoup(html, 'html5lib')
        self.root = HTMLNode(0, 0, 'body', depth=0)
        self.token_list = []

        ### I will use beautiful soup to parse the input HTML and do a pre-order traversal to generate my DomTree
        curr = (soup.body, self.root)
        # first element is beautiful soup tag(node), the second element is my Node
        stack: List[Tuple[Union[bs4.element.Tag, None], Node]] = [curr]
        node_idx = 1

        while curr != None and len(stack) != 0:
            curr = stack.pop()

            sib_idx = 0
            # all the children that are HTML nodes in beautiful soup Dom tree
            bs_HTML_children = curr[0].findChildren().copy()
            # curr[0].contents include not only children that are HTML nodes,
            # but also text node children
            bs_all_children = curr[0].contents

            if bs_all_children is None or len(bs_all_children) == 0:
                continue

            for child in bs_all_children:
                # if child is text node
                if len(bs_HTML_children) == 0 or child != bs_HTML_children[0]:
                    child_node = TextNode(node_idx, sib_idx, text=str(child).strip(), parent=curr[1], depth=curr[1].depth+1)
                    curr[1].add_child(child_node)
                # else if child is HTML node
                else:
                    bs_child = bs_HTML_children.pop(0)
                    class_list = bs_child.get("class") if bs_child.has_attr("class") else None
                    id = bs_child.get("id") if bs_child.has_attr("id") else None
                    child_node = HTMLNode(node_idx, sib_idx, tag=bs_child.name, class_list=class_list, id=id, parent=curr[1].tag, depth=curr[1].depth+1)
                    curr[1].add_child(child_node)
                    # append child to the stack
                    stack.append((bs_child, child_node))
                node_idx += 1
                sib_idx += 1

    def pre_order_traversal(self) -> Node:
        stack: List[Node] = self.root
        curr = [self.root]
        while curr != None and len(stack != 0):
            curr = stack.pop()
            yield curr
            if isinstance(curr, HTMLNode):
                for child in curr.children:
                    stack.append(child)

    def tokenize(self) -> List[Token]:
        position = 0
        tokens_lst: List[Token] = list()
        for node in self.pre_order_traversal():
            if isinstance(node, HTMLNode):
                tokens_lst.append(Token(position, tokenizer(node.tag), node))
                position += 1
                tokens_lst.append(Token(position, tokenizer(node.id), node))
                position += 1
                for class_ in node.class_list:
                    tokens_lst.append(Token(position, tokenizer(class_), node))
                    position += 1
            # else if is text node
            elif isinstance(node, TextNode):
                for word in node.text.split(" "):
                    tokens_lst.append(Token(position, tokenizer(word), node))
                    position += 1
        return tokens_lst


def tokenizer(str: str):
    tokenizer = BartTokenizer.from_pretrained("facebook/bart-large")
    return tokenizer(str)["input_ids"][1]