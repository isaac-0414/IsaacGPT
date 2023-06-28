from evaluation.eval import eval_websrc
from dotenv import load_dotenv
import os
import openai

# load secret keys from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY

if __name__ == '__main__':
    eval_websrc()