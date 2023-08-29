import openai
import os
from time import sleep
from processing.generate_response import generate_response
from dotenv import load_dotenv

def main():
    
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    openai.api_key = OPENAI_API_KEY
    
    print("\nISAAC: Hello I am ISAAC, your AI assistant, ask me anything :)")
    print("If you want to quit this conversation, you can simply type QUIT() or EXIT()")
    sleep(2)

    while True:
        user_input = input('\nUSER: ')
        if user_input == 'QUIT()' or user_input == 'EXIT()':
            return
        output = generate_response(user_input)
        print('\n\nISAAC: %s' % output)

if __name__ == '__main__':
    main()