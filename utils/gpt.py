import openai
import os
import re
from time import time, sleep
from .file_io import save_file 

def gpt3_embedding(content, engine='text-embedding-ada-002'):
    content = content.encode(encoding='ASCII',errors='ignore').decode()  # fix any UNICODE errors
    response = openai.Embedding.create(input=content,engine=engine)
    vector = response['data'][0]['embedding']  # this is a normal list
    return vector



def gpt3_completion(prompt, engine='text-davinci-003', temp=0.0, top_p=1.0, tokens=512, freq_pen=0.0, pres_pen=0.0, stop=['USER:', 'ISAAC:'], log=False):
    max_retry = 5
    retry = 0
    prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
    prompt = prompt.strip()
    while True:
        try:
            response = openai.Completion.create(
                engine=engine,
                prompt=prompt,
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                frequency_penalty=freq_pen,
                presence_penalty=pres_pen,
                stop=stop)
            text = response['choices'][0]['text'].strip()
            text = re.sub('[\r\n]+', '\n', text)
            text = re.sub('[\t ]+', ' ', text)
            filename = '%s_gpt3.txt' % time()
            if not os.path.exists('gpt3_logs'):
                os.makedirs('gpt3_logs')
            if log:
                save_file('gpt3_logs/%s' % filename, prompt + '\n\n==========\n\n' + text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "GPT3 error: %s" % oops
            print('Error communicating with OpenAI:', oops)
            sleep(1)

def gpt_chat(system_msg: str, user_msg: str, model="gpt-3.5-turbo", temp=0.0, top_p=1.0, tokens=1024, freq_pen=0.0, pres_pen=0.0, log=False):
    max_retry = 5
    retry = 0
    system_msg = system_msg.encode(encoding='ASCII',errors='ignore').decode()
    user_msg = user_msg.encode(encoding='ASCII',errors='ignore').decode()
    system_msg = system_msg.strip()
    user_msg = user_msg.strip()
    while True:
        try:
            completion = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                frequency_penalty=freq_pen,
                presence_penalty=pres_pen
            )
            text = completion.choices[0].message.content
            text = text.strip()
            text = re.sub('[\r\n]+', '\n', text)
            text = re.sub('[\t ]+', ' ', text)
            filename = '%s_gpt.txt' % time()
            if not os.path.exists('gpt_logs'):
                os.makedirs('gpt_logs')
            if log:
                save_file('gpt_logs/%s' % filename, system_msg + '\n\n==========\n\n' + user_msg + '\n\n==========\n\n' + text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "GPT 3.5/4 error: %s" % oops
            print('Error communicating with OpenAI:', oops)
            sleep(1)


def gpt3_chat(system_msg: str, user_msg: str, model="gpt-3.5-turbo", temp=0.0, top_p=1.0, tokens=1024, freq_pen=0.0, pres_pen=0.0, log=False):
    return gpt_chat(system_msg, user_msg, model, temp, top_p, tokens, freq_pen, pres_pen, log)


def gpt4_chat(system_msg: str, user_msg: str, model="gpt-4", temp=0.0, top_p=1.0, tokens=1024, freq_pen=0.0, pres_pen=0.0, log=False):
    return gpt_chat(system_msg, user_msg, model, temp, top_p, tokens, freq_pen, pres_pen, log)