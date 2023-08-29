import re

def remove_links(md: str):
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
    return re.sub(r'(\n\s*){3,}', '\n\n', md)