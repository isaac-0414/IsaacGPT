from googlesearch import search
from utils.gpt import gpt3_chat, gpt4_chat
from utils.gpt import gpt3_chat, gpt4_chat
from processing.URLloader import URLLoader
from processing.HTMLPreprocessor import HTMLPreprocessor
from utils.animations.spinner import Spinner
from utils.file_io import open_file
from typing import List
import re
import os
import math
import language_tool_python


def get_prompt_path(prompt: str) -> str:
    return os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'prompts', prompt))

def find_links_in_str(string: str) -> List[str]:
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(pattern, string)
    return urls

def generate_response(user_input: str) -> str:
    user_input = user_input.strip()

    with Spinner("Processing question..."):
        # Check question grammar
        is_bad_rule = lambda rule: rule.message == 'Possible spelling mistake found.' and len(rule.replacements) and rule.replacements[0][0].isupper()
        tool = language_tool_python.LanguageTool('en-US')
        matches = tool.check(user_input)
        matches = [rule for rule in matches if not is_bad_rule(rule)]
        user_input = language_tool_python.utils.correct(user_input, matches)

        # Remove all the contractions
        prompt_remove_contraction = "Remove all the contractions in the user's input.\n\ne.g.\nWhat's -> What is\nWho's -> Who is"
        user_input = gpt3_chat(prompt_remove_contraction, user_input)

    # If need to do math, then there can't be any stride, else some stride will help not to miss information
    with Spinner('Check whether need to count something'):
        question_need_count = f'Does this question start with phrase like "Find the number of" or "Count the number of" or "How many" or "What\'s the number of"? question: {user_input}'
        need_count_answer = gpt4_chat('', question_need_count)
        need_count_answer = need_count_answer.strip()
        if "Yes" in need_count_answer:
            need_count = True
            question_remove_count = f'In this sentence, replace phrase like "Find the number of" or "Count the number of" or "How many" or "What\'s the number of" to a single "Find". sentence: {user_input}'
            user_input = gpt4_chat('', question_remove_count)
        elif "No" in need_count_answer:
            need_count = False
        else:
            raise Exception('Need math return neither yes nor no.')
    
    with Spinner('Check would the answer be a list'):
        question_is_list = f'Would answer to this question "{user_input}" be a list? Start answer with "Yes" or "No"'
        is_list_answer = gpt4_chat('', question_is_list, log=True)
        is_list_answer = is_list_answer.strip()
        if "Yes" in is_list_answer:
            answer_is_list = True
        elif "No" in need_count_answer:
            answer_is_list = False
        else:
            raise Exception('would answer be a list return neither yes nor no.')
    
    with Spinner('Check what split size to use'):
        prompt_size = f"The user's question would be related to a webpage."
        size_answer = gpt4_chat(prompt_size, f'Question: {user_input}\nIs this question about one or some specific thing on the webpage? Answer Yes or No.', log=True)
        size_answer = size_answer.strip()

        if "yes" in size_answer or "Yes" in size_answer:
            use_large_split = False
        elif "no" in size_answer or "No" in size_answer:
            use_large_split = True
        else:
            raise Exception('[Split size] return neither yes nor no')
    

    # do a Google Search
    prompt_query = f'Provide the best query to search Google to find answer to the question "{user_input}"'
    query = gpt4_chat('', prompt_query, log=True)
    if query.startswith('\"'):
        query = query[1:-1]
    with Spinner('Searching Google...'):
        google_result = search(query, num_results=5)
    urls_stack =  list(google_result)
    urls_visited = []
    webpages_info = []
    answers_wp = []

    num_iter = 0
    while num_iter < 1 and not len(urls_stack) == 0:
        num_iter += 1
        url = urls_stack.pop(0)
        # if visited this url before, continue to next iteration
        if url in urls_visited:
            continue
        # else add this url to the set
        urls_visited.append(url)

        answer_wp = None # this would be the answer after reading this webpage
    
        # Fetch and download the webpage
        with Spinner("Fetching a new webpage... "):
            loader = URLLoader(url=url, headless=True)
            html = loader.load()
        preprocessor = HTMLPreprocessor(html=html, base_url=url)

        # summarize the webpage
        with Spinner('Summarizing this webpage'):
            wp_summary = preprocessor.summarize()

        # check whether should look at this webpage
        with Spinner('Checking whether this webpage is worth looking...'):
            sys_prompt_info = f'Here is some information about one webpage:\n\nTitle: {preprocessor.title}\n\nSummary: {wp_summary}'
            user_prompt_info = f'Do you think the content on this webpage may contain information to answer the question: {user_input}'
            answer_should_look = gpt4_chat(sys_prompt_info, user_prompt_info, log=True)
            should_look = answer_to_yesno(question=user_prompt_info, answer=answer_should_look)
            if not should_look:
                continue

        # save information of webpage
        webpages_info.append({'title': preprocessor.title, 'summary': wp_summary})

        # Find useful hyperlinks and push them to the stack
        with Spinner('Finding hyperlinks on this page...'):
            hyperlinks = preprocessor.hyperlinks
            num_parts = math.ceil(len(hyperlinks) / 50)
            for i in range(num_parts):
                links_group = hyperlinks[50 * i : (50 * i + 50) if (50 * i + 50) < len(hyperlinks) else len(hyperlinks)]
                links_group_str = '\n'.join(links_group)
                # ask gpt links to follow
                sys_prompt_link = f'Here is some information about a webpage:\n\nURL of the webpage:{url}\n\nTitle of the webpage: {preprocessor.title}\n\nSummary of the webpage: {wp_summary}\n\nHere are some hyperlinks found on this webpage:\n{links_group_str}'
                user_prompt_link = f'I am trying to find answer to the question "{user_input}", do you think reading this webpage is enough to answer this question, is there any hyperlinks on this webpage that is necessary to answer the question?'
                links_res = gpt4_chat(sys_prompt_link, user_prompt_link, log=True)
                links_to_follow = find_links_in_str(links_res)
                # push useful links to the urls stack
                urls_stack = links_to_follow + urls_stack
        
        if use_large_split:
            answers = list()
            split_large = preprocessor.build_split(window_size=10000, stride=8000)
            for i, chunk in enumerate(split_large):
                with Spinner(f"Generating answers(large split), progress: {i}/{len(split_large)}"):
                    prompt_answer = open_file(get_prompt_path('answer.txt')).replace('<<TITLE>>', preprocessor.title).replace('<<CONTEXT>>', chunk)
                    answer = gpt4_chat(prompt_answer, user_input, log=True)
                    answers.append(answer)
            answer_wp = put_answers_together(user_input, answers, answer_is_list=answer_is_list)
        else:
            # first go over split with a small window size
            answers = list()
            split_small = preprocessor.build_split(window_size=2000, stride=1800)
            for i, chunk in enumerate(split_small):
                with Spinner(f"Generating answers(small split), progress: {i}/{len(split_small)}"):
                    prompt_answer = open_file(get_prompt_path('answer.txt')).replace('<<TITLE>>', preprocessor.title).replace('<<CONTEXT>>', chunk)
                    answer = gpt4_chat(prompt_answer, user_input, log=True)
                    answers.append(answer)
            answer_wp = put_answers_together(user_input, answers, answer_is_list=answer_is_list)

            # then go over all the parts with similar structure, which usually contains important information
            try:
                lists_answers = list()
                split_list = preprocessor.build_lists_split(window_size=2000)
                if (len(split_list) == 0):
                    raise Exception('split all too large, not worth looking')
                for i, chunk in enumerate(split_list):
                    with Spinner(f"Generating answers(lists), progress: {i}/{len(split_list)}"):
                        prompt_answer = open_file(get_prompt_path('answer.txt')).replace('<<TITLE>>', preprocessor.title).replace('<<CONTEXT>>', chunk)
                        answer = gpt4_chat(prompt_answer, user_input, log=True)
                        lists_answers.append(answer)
                lists_answer_wp = put_answers_together(user_input, lists_answers, answer_is_list=answer_is_list)
                answer_wp = put_answers_together(user_input, [answer_wp, lists_answer_wp], answer_is_list=answer_is_list)
            except Exception as oops:
                print('Error going over the "list", skip over it for now:', oops)

        answers_wp.append(answer_wp)

        # check whether the information that have been seen is enough to get an answer, if so, end the loop
        with Spinner('Check whether should stop...'):
            sys_prompt_enough = 'Here is some information about one or some webpages:\n'
            for i, webpage_info in enumerate(webpages_info):
                sys_prompt_enough += f'\n______\n{i}.\nTitle: {webpage_info["title"]}\n\nSummary: {webpage_info["summary"]}'
            user_prompt_enough = f'Do you think the content on these webpages provides enough information to answer the question: {user_input}'
            answer_enough = gpt4_chat(sys_prompt_enough, user_prompt_enough, log=True)

            info_enough = answer_to_yesno(question=user_prompt_enough, answer=answer_enough)
            if info_enough:
                break
    
    # Combine all the answers to a final answer
    if answer_is_list:
        final = "\n\n".join([f"Answer according to webpage {urls_visited[i]}" + answers_wp[i] for i in range(len(answers_wp))])
    else:
        final = put_answers_together(user_input, answers_wp, count_number=need_count, answer_is_list=False)
    return final
        

def put_answers_together(user_input, answers, count_number=False, answer_is_list=False):
    if len(answers) == 1:
        return answers
    
    if answer_is_list or count_number:
        with Spinner('formatting and putting answers together'):
            formatted_answers = []

            for answer in answers:
                if 'None' not in answer and 'NONE' not in answer:
                    sys_prompt_format = 'Here is answer to one question:\n\n' + answer
                    user_prompt_format = 'Write this answer in this format:\ne.g.\nThe students graduating in 2024 are Isaac Zheng and Mark Zhang should be written in this format:\n- Isaac Zheng\n- Mark Zhang'
                    formatted_answer = gpt4_chat(sys_prompt_format, user_prompt_format)
                    formatted_answers.append(formatted_answer)
            
            answer_lines: list[str] = []

            for answer in formatted_answers:
                answer_lines += answer.split('\n')

            # remove all the punctuations and decorators at the beginning of each line
            answer_lines = [re.sub(r'^[-*\d.]+', '', answer_line.strip()).strip() for answer_line in answer_lines]

            # remove duplicates in this list
            i = 0
            while i < len(answer_lines):
                j = 0
                while j < len(answer_lines):
                    if j != i:
                        # if one element is in another element, remove it
                        if answer_lines[i] in answer_lines[j]:
                            answer_lines.pop(i)
                            i -= 1
                            break
                    j += 1
                i += 1
            if count_number:
                return len(answer_lines)
            
            final = '\n'.join(answer_lines)
            with open('temp.txt', 'w') as f:
                f.write(final)

    else:
        with Spinner('Putting answers together...'):
            answers = [f'part{i+1}: ' + answer for i, answer in enumerate(answers)]
            answers_str = '\n\n'.join(answers)
            prompt_summary = open_file(get_prompt_path('put_together.txt')).replace('<<QUESTION>>', user_input).replace('<<ANSWERS>>', answers_str)
            put_together_prompt = f'Based on answers, generate a final answer to the question "{user_input}"'
            final = gpt4_chat(prompt_summary, put_together_prompt)
    return final


def answer_to_yesno(question: str, answer: str) -> bool:
    sys_prompt = f'Question: {question}\n\nAnswer: {answer}'
    user_prompt = 'Is this answer a "Yes" answer or a "No" answer?'
    yesno_answer = gpt4_chat(sys_prompt, user_prompt)
    if 'yes' in yesno_answer or 'Yes' in yesno_answer:
        return True
    elif 'no' in yesno_answer or 'No' in yesno_answer:
        return False
    else:
        raise Exception('answer_to_yesno contain neither yes nor no')
        