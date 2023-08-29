from typing import Union

def split_text_by_char_len(input: str, window_size: int=6000, stride: Union[int, None]=3000):
    """
    Split the text based on number of characters. It would only breaks a document if there is a line
    break, if not, it would go back until hits a line break. You can also set the overlap by the "stride"
    argument.

    Parameters:
    input (str): the input document to be split
    window_size (int): the length of each chunk of split in number of characters
    stride (int or None): e.g. if stride=3000, the distance between the starts of two chunks are 3000 characters.

    Returns:
    List[str]: the split
    """
    start = 0
    end = 0
    result = list()
    while start + window_size <= len(input):
        end = start + window_size
        while input[end - 1] != '\n' and end > start:
            end -= 1
        if end <= start:
            end = start + window_size
        result.append(input[start:end])
        if stride == 0 or stride is None:
            start = end
        else:
            start_tmp = start
            start += stride
            while input[start - 1] != '\n' and start > start_tmp:
                start -= 1
            if start <= start_tmp:
                start = start_tmp + stride
    
    if start + window_size > len(input):
        result.append(input[start:len(input)])
    return result

