from .similarity import cosine_similarity
import json
import os

class VDB:
    def __init__(self, vdb_file: str):
        self.vdb_file = vdb_file
        with open(vdb_file, 'w') as f:
            json.dump([], f)

    # query the most similar vectors from the vector database
    def query_index(self, vector, count: int=15):
        with open(self.vdb_file, 'r') as infile:
            data = json.load(infile)
        
        scores = list()
        for i in data:
            score = cosine_similarity(vector, i['vector'])
            #print(score)
            scores.append({'content': i['content'], 'score': score})
        ordered = sorted(scores, key=lambda d: d['score'], reverse=True)
        ordered_content = [x['content'] for x in ordered]
        return scores

    # insert data into the vector database
    def insert_index(self, in_data):
        # if not isinstance(in_data, dict) or in_data["content"] is None or in_data["vector"] is None:
        #     raise ValueError("input when inserting to vector database should be a dict {'content': ..., 'vector': ...}")
        data = []
        # Read existing data from file
        with open(self.vdb_file, 'r') as infile:
            data = json.load(infile)

        # append new data to the end of old data
        if isinstance(in_data, list):
            data = data + in_data
        else:
            data.append(in_data)

        # Write updated data back to file
        with open(self.vdb_file, 'w') as outfile:
            json.dump(data, outfile, indent=2)

    # empty the current database file
    def empty_db(self):
        with open(self.vdb_file, 'w') as f:
            json.dump({}, f)