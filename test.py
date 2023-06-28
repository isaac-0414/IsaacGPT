from transformers import BartTokenizer, AutoModelForSeq2SeqLM
import torch

with open("data.md", "r") as f:
    content = f.read()

chunks = content.split("______")

device = 'cuda' if torch.cuda.is_available() else 'cpu'
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(device))
    print("Use", torch.cuda.device_count(), "GPU(s)")
else:
    print("Use CPU")

tokenizer = BartTokenizer.from_pretrained("facebook/bart-large")

model = AutoModelForSeq2SeqLM.from_pretrained("./models/md_completion_model/")
model = model.to(device)

def split_str_by_num_words(input: str, split_size: int=1000):
    words = list()
    word = ""
    start = 0
    for i, c in enumerate(input):
        if c == " ":
            if word != "":
                words.append({"word": word, "start": start, "end": i})
                word = ""
            else:
                continue
        elif len(word) >= 5:
            words.append({"word": word, "start": start, "end": i})
            if c == "\n":
                words.append({"word": "\n", "start": i, "end": i+1})
                word = ""
            else:
                word = c
                start = i
        elif c == "\n":
            if word != "":
                words.append({"word": word, "start": start, "end": i})
            words.append({"word": "\n", "start": i, "end": i+1})
            word = ""
        else:
            if word == "":
                start = i
            word += c
    words.append({"word": word, "start": start, "end": len(input)})

    result = list()
    start_idx = 0
    while start_idx < len(words):
        start = words[start_idx]["start"]

        if start_idx + split_size - 1 < len(words):
            end_idx = start_idx + split_size - 1
            end_idx_save = end_idx
            while words[end_idx]["word"] != "\n" and end_idx > start_idx:
                end_idx -= 1
            if end_idx <= start_idx:
                end_idx = end_idx_save
        else:
            end_idx = len(words) - 1

        end =  words[end_idx]["end"]
        result.append(input[start : end])

        start_idx = end_idx + 1

    return result

processed_md = list()

for chunk in chunks:
    chunk_split = split_str_by_num_words(chunk, 800)
    result = ""
    for split in chunk_split:
        input_ids = tokenizer([split], return_tensors="pt", max_length=1024, padding='max_length', truncation=True)["input_ids"]
        output_ids = model.generate(input_ids.to(device), min_length=0, max_length=1024)
        output = tokenizer.batch_decode(output_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        result += output + '\n'
    processed_md.append(result)

with open("output.md", 'w', encoding='utf-8') as outfile:
    outfile.write("\n______\n".join(processed_md))