import openai
import os
from time import sleep
from utils.file_io import open_file, empty_folder
from processing.generate_response import generate_response
from utils.vdb import VDB
from utils.nexus import save_nexus, load_nexus
from dotenv import load_dotenv

def clear_memory():
    dir = os.path.dirname(__file__)
    nexus = os.path.join(dir, 'memory','nexus')
    empty_folder(nexus)
    dir = os.path.dirname(__file__)
    text_and_docs = os.path.join(dir, 'memory','text&docs')
    empty_folder(text_and_docs)
    dir = os.path.dirname(__file__)
    thinking_process = os.path.join(dir, 'memory','thinking_process')
    empty_folder(thinking_process)
    dir = os.path.dirname(__file__)
    vdb = os.path.join(dir, 'memory','vdb')
    empty_folder(vdb)

def main():
    # Our chatbot will generate new response based on 15 most relevant previous conversations
    convo_length = 10

    # load secret keys from .env file
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    openai.api_key = OPENAI_API_KEY
    
    # empty the memory first
    clear_memory()

    # our vector database to save all the vectorized conversations
    dir = os.path.dirname(__file__)
    vdb_file = os.path.join(dir, 'memory','vdb','nexus_vectors.json')
    vdb = VDB(vdb_file)
    
    print("\nISAAC: Hello I am ISAAC, your AI assistant, ask me anything :)")
    print("If you want to quit conversation, you can simply type QUIT() or EXIT()")
    sleep(2)

    while True:
        #### get user input, save it, vectorize it, save it to vector database
        payload = list() # payload will contain information of the current conversation and will be saved to vdb
        user_input = input('\nUSER: ')
        if user_input == 'QUIT()' or user_input == 'EXIT()':
            return

        unique_id, vector = save_nexus(user_input)
        # saving id of conversation to the vector database
        payload.append({'content': unique_id, 'vector': vector})
        print()
        #### search for relevant messages, and generate a response
        conv_ids = vdb.query_index(vector=vector, count=convo_length)
        conversation = load_nexus(conv_ids)  # results should be a DICT with 'matches' which is a LIST of DICTS, with 'id'

        #### generate response, vectorize, save, etc
        output = generate_response(conversation, user_input)

        unique_id, vector = save_nexus(output)
        payload.append({'content': unique_id, 'vector': vector})
        vdb.insert_index(payload)
        print('\n\nISAAC: %s' % output)

if __name__ == '__main__':
    main()