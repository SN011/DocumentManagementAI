import os
from langchain_community.document_loaders import PyPDFDirectoryLoader, PyPDFLoader, WebBaseLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, TextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain.agents.agent_toolkits import ZapierToolkit
from docx import Document
from langchain.agents import initialize_agent , create_structured_chat_agent, AgentType
from groq import Groq
import random
from langchain_groq import ChatGroq

def init_groq():
    api_keys = ['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','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',
                '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','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']

    client = Groq(
        
        api_key = random.choice(api_keys)
    )

    llm = ChatGroq(groq_api_key = client.api_key,
                model_name = "llama3-70b-8192")
    
    return client, llm