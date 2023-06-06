from time import time
from uuid import uuid4
from .file_io import open_file, save_json, load_json
from .gpt3 import gpt3_embedding
from .time import timestamp_to_datetime

def load_nexus(ids):
    result = list()
    for id in ids:
        info = load_json('memory/nexus/%s.json' % id)
        result.append(info)
    ordered = sorted(result, key=lambda d: d['time'], reverse=False)  # sort them all chronologically
    messages = [i['message'] for i in ordered]
    return '\n'.join(messages).strip()

def save_nexus(message):
    timestamp = time()
    timestring = timestamp_to_datetime(timestamp)
    vector = gpt3_embedding(message)
    unique_id = str(uuid4())
    metadata = {'speaker': 'USER', 'time': timestamp, 'message': message, 'timestring': timestring, 'uuid': unique_id}
    save_json('memory/nexus/%s.json' % unique_id, metadata)
    return unique_id, vector