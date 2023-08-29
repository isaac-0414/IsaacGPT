import re

def remove_links(md: str):
    """
    Remove all the links on the markdown document

    Parameters:
    md (str): the input markdown doc
    
    Returns:
    str: processed markdown
    """
    to_return = ""
    is_link = False
    for i in range(len(md)):
        if is_link and md[i] == ')':
            is_link = False
            continue
        if is_link:
            continue
        if md[i] == ']' and i + 1 < len(md) and md[i+1] == '(':
            is_link = True
        to_return += md[i]
    
    return to_return

def format_md(md: str):
    """
    Remove special characters and spaces at the beginning and end of line

    Parameters:
    md (str): the input markdown doc
    
    Returns:
    str: processed markdown
    """
    lines = md.split('\n')
    for i in range(1, len(lines)):
        lines[i] = lines[i].strip()
        specials = [']', ')', '>', ',', '.', ';', ':']
        while len(lines[i]) > 0 and lines[i][0] in specials:
            lines[i-1] += ' ' + lines[i][0]
            lines[i] = lines[i][1:]
            lines[i] = lines[i].strip()
    return '\n'.join(lines)

def remove_multi_line_breaks(md: str):
    """
    Remove consecutive multiple line breaks

    Parameters:
    md (str): the input markdown doc
    
    Returns:
    str: processed markdown
    """
    return re.sub(r'(\n\s*){3,}', '\n\n', md)