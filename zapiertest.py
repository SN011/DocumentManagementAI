# %%
# !pip install --upgrade langchain
#!pip install --upgrade langchain-groq
# !pip install -U langchain-community

# %%
import os
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFDirectoryLoader, PyPDFLoader, WebBaseLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain.agents.agent_toolkits import ZapierToolkit

from langchain.utilities.zapier import ZapierNLAWrapper
from langchain.agents import initialize_agent , AgentType
import random
from groq import Groq
import streamlit as st
api_keys = ['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','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',
            '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','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']

client = Groq(
    
    api_key = random.choice(api_keys)
)

llm = ChatGroq(groq_api_key = client.api_key,
               model_name = "llama3-70b-8192")

# %%
from cryptography.fernet import Fernet
import base64
from dotenv import load_dotenv
import os
# Load environment variables from .env
load_dotenv()
with open('C:\\Users\\pc-user1\\Desktop\\key.txt', 'r') as file:
    k = file.read().strip()[2:-1]
    #k = base64.urlsafe_b64decode(k.encode())


# Decode and decrypt the API key
encoded_encrypted_api_key = os.getenv("ENCRYPTED_API_KEY")
encrypted_api_key = base64.b64decode(encoded_encrypted_api_key)
decipher_suite = Fernet(k)


# %%
zapier = ZapierNLAWrapper(zapier_nla_api_key=decipher_suite.decrypt(encrypted_api_key).decode())
toolkit = ZapierToolkit.from_zapier_nla_wrapper(zapier)
from langchain.agents import Tool
my_tools = []
for tool in toolkit.tools:
    my_tools.append(tool)



def write_file(input=""):
    with open(os.getcwd()+'\\main.cpp','w') as file:
        file.write("""#include <iostream> \n\n using namespace std; \n\n int main()\n{\ncout<<"Hello World!"<<endl;\nreturn 0;\n}\n""")
my_tools.append(Tool(name="write-file",func=write_file, description="useful when user asks you to c++ hello world code to a file"))
agent = initialize_agent(my_tools,llm,agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,verbose=True)

# %%
for tool in my_tools:
    print(tool.name)
    print(tool.description)
    print("\n\n")

# %%
agent.invoke({"input":"""
BEFORE PROCEEDING, FIND THE GOOGLE DOC WITH THE SAME TITLE.
Can you please put ALL OF THE FOLLOWING the following into a formatted google document for a renovation quote contract? 
YOU MUST FORMAT THE CONTENT PROPERLY BEFORE WRITING IT INTO DOC.
          THE TEXT: 'RENOVATION QUOTE

**Project Overview:**
- Project Description: Basement renovation project in Herndon, VA 20170
- Length of Time for Project: Not specified

**Cost Breakdown:**

1. **Labor Costs:**
   - Total Labor Cost: $45,000
   
2. **Material Costs:**
   - Total Material Cost: $33,500
   - Itemized Costs:
     + Flooring: $5,000
     + Lighting: $3,000
     + Shelving: $3,500
     + Mirror and Decor: $1,000
     + Seating and Furniture: $4,000
     + Hot Tub and Glass Wall: $8,000
     + Electrical and HVAC: $6,000
     + Miscellaneous: $3,000

**Total Estimated Cost:**
- Total Cost of Labor: $45,000
- Total Cost of Materials: $33,500
- **Grand Total: $78,500**

**Payment Terms:**
- Deposit Required: 20% of the total estimated cost ($15,700.00)
- Payment Schedule: Monthly payments for 6 months, with the final payment due upon completion of the project
- Monthly Payment: $10,466
- Final Payment Due: Upon completion of the project'

"""})

# %%
agent.invoke({"input":"YOU MUST WRITE C++ HELLO WWORLD CODE TO A FILE - USE THE write-file TOOL. thats all"})


