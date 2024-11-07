from tools.imports import *

api_key = 'csk-ty83w2vfvtxj2ecw3h5cfxcx3dxx2xfjry58em8j2kdwexx4'

def init_cerebras():
    
    client = Cerebras(
        
        api_key = api_key
    )

    llm = ChatCerebras(api_key= client.api_key,
                model_name = "llama3.1-70b", streaming=True)
    
    return client, llm