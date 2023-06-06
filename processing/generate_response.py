from utils.gpt3 import gpt3_completion
from utils.web.visit_url import fetch_HTML_content_from_url
from utils.web.html_util import get_body_from_html
from utils.animations.spinner import Spinner
from utils.file_io import open_file
from utils.summarize import summarize
import os
import textwrap


def generate_response(conversation, user_input, engine='text-davinci-003', temp=0.0, top_p=1.0, tokens=400, freq_pen=0.0, pres_pen=0.0):
    url = input('Please give me a URL of a webpage for reference: ')
    url = url.strip()
    #### Fetch and download the webpage
    with Spinner("Fetching webpages... "):
        save_wp_path=os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'memory', 'webpages', 'index.html'))
        html_content = fetch_HTML_content_from_url(url=url, save_file_path=save_wp_path)
        html_body_content = get_body_from_html(html_content)
    # If webpage short, look at the entire webpage and try to solve the problem
    if len(html_body_content) <= 4000:
        with Spinner('Thinking and generating response...'):
            file_path=os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'short_wp.txt'))
            prompt_short_wp = open_file(file_path).replace('<<CONVERSATION>>', conversation).replace('<<MESSAGE>>', user_input).replace('<<WEBPAGE>>', html_body_content)
            final = gpt3_completion(prompt_short_wp, engine, temp, top_p, tokens, freq_pen, pres_pen, stop=['USER:', 'ISAAC:'])
        #### Self criticize this answer
        with Spinner("Self criticizing this answer..."):
            # I added this for loop in case GPT make a mistake, returned results not in the desired format, I will give it 2 chances.
            for i in range(3):
                file_path=os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'self_criticize', 'self_criticize_short.txt'))
                prompt_self_criticize = open_file(file_path).replace('<<CONVERSATION>>', conversation).replace('<<MESSAGE>>', user_input).replace('<<WEBPAGE>>', html_body_content).replace('<<MY ANSWER>>', final)
                criticism = gpt3_completion(prompt_self_criticize, engine, temp, top_p, tokens, freq_pen, pres_pen, stop=['USER:', 'ISAAC:'])
                if criticism.startswith("[YES]") or criticism.startswith("[NO]"):
                    break
                if i == 2:
                    # if still not in the desired format, throw an Error
                    raise RuntimeError("GPT is not working as expected")
            
        if criticism.startswith("[YES]"):
            # The result is good, jump to end
            pass
        elif criticism.startswith("[NO]"):
            with Spinner('Reading webpage again and generating a better answer...'):
                # The result is not good, split advice from the result and generate answer again
                advice = criticism[4:]
                file_path=os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'self_criticize', 'short_wp_again.txt'))
                prompt_short_wp_again = open_file(file_path).replace('<<CONVERSATION>>', conversation).replace('<<MESSAGE>>', user_input).replace('<<WEBPAGE>>', html_body_content).replace('<<MY ANSWER>>', final).replace('<<MY ADVICE>>', advice)
                criticism = gpt3_completion(prompt_short_wp_again, engine, temp, top_p, tokens, freq_pen, pres_pen, stop=['USER:', 'ISAAC:'])
        else:
            raise RuntimeError("This is not supposed to happen, an RuntimeError should have be raised already")
                
    else:
        with Spinner("Reading at the webpage in detail and try to get an answer..."):
            #### First try to summarize the webpage to get an overall idea
            overall_idea = summarize(html_body_content, length=4)
            
            #### Then divide webpage into chunks and look into each chunk
            chunks = textwrap.wrap(html_body_content, 4000)
            responses_n_summaries = list()
            for idx, chunk in enumerate(chunks):
                # generating summary of each chunk for later step
                file_path=os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'summarize_webpage.txt'))
                prompt_summary = open_file(file_path).replace('<<MESSAGE>>', user_input).replace('<<WEBPAGE>>', chunk)
                chunk_summary = gpt3_completion(prompt_summary, engine, temp, top_p, tokens, freq_pen, pres_pen, stop=['USER:', 'ISAAC:'])
                
                # Looking into each chunk, and try to solve the problem
                file_path=os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'wp_chunk.txt'))
                prompt_entire_wp = open_file(file_path).replace('<<CONVERSATION>>', conversation).replace('<<MESSAGE>>', user_input).replace('<<CHUNK>>', chunk).replace('<<SUMMARY>>', overall_idea)
                chunk_response = gpt3_completion(prompt_entire_wp, engine, temp, top_p, tokens, freq_pen, pres_pen, stop=['USER:', 'ISAAC:'])
                
                summary_str = f"Summary of chunk{idx + 1}: " + chunk_summary
                response_str = f"Response corresponding to chunk{idx + 1}: " + chunk_response
                responses_n_summaries.append({"summary": summary_str, "response": response_str})

        with Spinner("Looking at the webpage from a higher level and try to get an answer..."):
            # concat all answers together
            all_responses = "\n\n".join([d["summary"] + "\n\n" + d["response"] for d in responses_n_summaries])

            #### Then try to solve the problem from a higher level, looking at results of all parts together
            file_path=os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'wp_overall.txt'))
            prompt_wp_overall = open_file(file_path).replace('<<CONVERSATION>>', conversation).replace('<<MESSAGE>>', user_input).replace('<<SUMMARY>>', overall_idea).replace('<<CHUNK RESPONSES AND SUMMARY>>', all_responses)
            final = gpt3_completion(prompt_wp_overall, engine, temp, top_p, tokens, freq_pen, pres_pen, stop=['USER:', 'ISAAC:'])

        #### Self criticize this answer
        with Spinner("Self criticizing this answer..."):
            # concat all the summaries together
            chunk_summaries = "\n\n".join([d["summary"] for d in responses_n_summaries])
            # I added this for loop in case GPT make a mistake, returned results not in the desired format, I will give it 2 chances.
            for i in range(3):
                file_path=os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'self_criticize', 'self_criticize_long.txt'))
                prompt_self_criticize = open_file(file_path).replace('<<CONVERSATION>>', conversation).replace('<<MESSAGE>>', user_input).replace('<<SUMMARY OF WEBPAGE>>', overall_idea).replace('<<SUMMARY OF CHUNKS>>', chunk_summaries).replace('<<MY ANSWER>>', final)
                criticism = gpt3_completion(prompt_self_criticize, engine, temp, top_p, tokens, freq_pen, pres_pen, stop=['USER:', 'ISAAC:'])
                
                # checking format
                try:
                    if criticism.startswith("[YES]"):
                        break
                    elif criticism.startswith("[NO]"):
                        substr = criticism[4:]
                        start = 1
                        end = substr.find("]")
                        chunk_indices_str = substr[start:end]
                        chunk_indices = chunk_indices_str.split(", ")
                        chunk_indices = [int(i) - 1 for i in chunk_indices]
                        break

                except Exception as oops:
                    if i == 2:
                        # if still not in the desired format, throw an Error
                        raise RuntimeError("GPT is not working as expected")
            
        if criticism.startswith("[YES]"):
            # The result is good, jump to end
            pass
        elif criticism.startswith("[NO]"):
            with Spinner('Reading webpage again and generating a better answer...'):
                # The result is not good, split chunks that need to be looked at again and advice from the result and generate answer again
                substr = criticism[4:]
                start = 1
                end = substr.find("]")
                # converting string of the form '1, 3, 4' to list [1, 3, 4]
                chunk_indices_str = substr[start:end]
                chunk_indices = chunk_indices_str.split(", ")
                chunk_indices = [int(i) - 1 for i in chunk_indices]
                # split out advice
                advice = substr[end+1:]

                updated_chunk_responses = list()

                for idx in chunk_indices:
                    chunk_summary = responses_n_summaries[idx]["summary"]
                    
                    file_path=os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'self_criticize', 'wp_chunk_again.txt'))
                    prompt_wp_chunk_again = open_file(file_path).replace('<<CONVERSATION>>', conversation).replace('<<MESSAGE>>', user_input).replace('<<CHUNK>>', chunk).replace('<<SUMMARY>>', overall_idea).replace('<<MY ANSWER>>', final).replace('<<MY ADVICE>>', advice)
                    criticism = gpt3_completion(prompt_wp_chunk_again, engine, temp, top_p, tokens, freq_pen, pres_pen, stop=['USER:', 'ISAAC:'])
                    updated_chunk_responses.append(f"Updated response after looking into chunk{idx} again: " + chunk_response)
                # concat all answers together
                chunk_summaries = "\n\n".join([d["summary"] for d in responses_n_summaries])
                updated_responses = "\n\n".join(updated_chunk_responses)

                # Then combine the new answers together
                file_path=os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'self_criticize', 'wp_overall_again.txt'))
                prompt_wp_overall_again = open_file(file_path).replace('<<CONVERSATION>>', conversation).replace('<<MESSAGE>>', user_input).replace('<<MY ANSWER>>', final).replace('<<MY ADVICE>>', advice).replace('<<UPDATED RESPONSES>>', updated_responses)
                final = gpt3_completion(prompt_wp_overall_again, engine, temp, top_p, tokens, freq_pen, pres_pen, stop=['USER:', 'ISAAC:'])
            
        else:
            raise RuntimeError("This is not supposed to happen, an RuntimeError should have be raised already")


    #### TODO: Then look at all the links on this page and think about are there any useful links should follow

    #### Add an open-ended question if there is not one
    with Spinner('Finalizing my answer...'):
        file_path=os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'open_end.txt'))
        prompt_open_end = open_file(file_path).replace('<<CONVERSATION>>', conversation).replace('<<MESSAGE>>', user_input).replace('<<ANSWER>>', final)
        final = gpt3_completion(prompt_open_end, engine, temp, top_p, tokens, freq_pen, pres_pen, stop=['USER:', 'ISAAC:'])

    return final