from transformers import BartTokenizer, AutoModelForSeq2SeqLM
import torch

def markdown_completion(markdown: str):
   device = 'cuda' if torch.cuda.is_available() else 'cpu'
   if torch.cuda.is_available():
      print(torch.cuda.get_device_name(device))
      print("Use", torch.cuda.device_count(), "GPU(s)")
   else:
      print("Use CPU")

   tokenizer = BartTokenizer.from_pretrained("facebook/bart-large")

   model = AutoModelForSeq2SeqLM.from_pretrained("./models/md_completion_model/")
   model = model.to(device)

   input_ids = tokenizer([markdown], return_tensors="pt", max_length=1024, padding='max_length', truncation=True)["input_ids"]
   output_ids = model.generate(input_ids.to(device), min_length=0, max_length=1024)
   output = tokenizer.batch_decode(output_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
   return output