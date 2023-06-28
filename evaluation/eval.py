"""Evaluate the model, currently GPT 3.5"""
import os
import evaluate
import pandas as pd
from utils.file_io import open_file
from utils.gpt3 import gpt3_completion
from utils.animations.spinner import Spinner
from langchain.docstore.document import Document
from readabilipy import simple_tree_from_html_string
from html2text import html2text


def eval_websrc():
    data_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'data', 'WebSRC'))

    test_split = [
        {"category": "auto", "indices": ["01", "08"]},
        {"category": "book", "indices": ["17"]},
        {"category": "game", "indices": ["09", "12"]},
        {"category": "jobs", "indices": ["11"]},
        {"category": "movie", "indices": ["2"]},
        {"category": "phone", "indices": ["4"]},
        {"category": "sports", "indices": ["9", "10"]}
    ]

    # load squad for validation, which contains EM and F1
    squad_metric = evaluate.load("squad")

    for d in test_split:
        predictions = []
        references = []
        for idx in d["indices"]:
            dataset_path = os.path.join(data_path, d["category"], idx, "dataset.csv")
            df = pd.read_csv(dataset_path)
            num_rows = len(df.index)
            for row_idx, row in df.iterrows():
                with Spinner(f"Processing data in {d['category']} folder, progress: [{row_idx}/{num_rows}]"):
                    question = row["question"]
                    answer = row["answer"]
                    id = row["id"]
                    # answer_start seems doesn't matter here
                    references.append({'answers': {'answer_start': [0], 'text': [answer]}, 'id': id})

                    html_path = os.path.join(data_path, d["category"], idx, "processed_data", f"{id[2:9]}.html")
                    html = open_file(html_path)
                    ### preprocess HTML content
                    simple_tree = simple_tree_from_html_string(html)
                    # html2text is used to convert html to markdown
                    text = html2text(str(simple_tree))
                    metadata = {"id": id}
                    doc = Document(page_content=text, metadata=metadata)
                    markdown = doc.page_content

                    # generate response with GPT 3.5
                    prompt_path = os.path.realpath(os.path.join(os.path.dirname(__file__), 'QA_prompt.txt'))
                    prompt = open_file(prompt_path).replace('<<WEBPAGE>>', markdown).replace('<<QUESTION>>', question)
                    result = gpt3_completion(prompt, log=True)
                    predictions.append({'prediction_text': result, 'id': id})
        ### Compute the EM and F1 score of this category
        squad_result = squad_metric.compute(predictions=predictions, references=references)
        print(f"============== {d['category']} ==============")
        print(squad_result)