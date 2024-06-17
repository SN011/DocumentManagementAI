# %%
# !pip install streamlit
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
if "vector" not in st.session_state:
    st.session_state.embeddings = HuggingFaceEmbeddings()
    
    st.session_state["loader"] = WebBaseLoader("https://docs.smith.langchain.com/")
    st.session_state["docs"] = st.session_state["loader"].load() 

    st.session_state["text_splitter"] = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
    st.session_state["final_documents"] = st.session_state["text_splitter"].split_documents(st.session_state["docs"])
    st.session_state["vectors"] = FAISS.from_documents(st.session_state["final_documents"],st.session_state.embeddings)

# embeddings = HuggingFaceEmbeddings()

# loader = WebBaseLoader("https://docs.smith.langchain.com/")
# docs = loader.load() 

# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
# final_documents = text_splitter.split_documents(docs)
# vectors = FAISS.from_documents(final_documents,embeddings)



st.title("Doc Mgr")
prompt = ChatPromptTemplate.from_template(
"""
Answer the questions based on the provided context only.
Please provide the most accurate response based on the question
<context>
{context}
<context>
Questions:{input}
"""
)

# %%
document_chain = create_stuff_documents_chain(llm,prompt)
retriever = st.session_state.vectors.as_retriever()
#retriever = vectors.as_retriever()
retrieval_chain = create_retrieval_chain(retriever, document_chain)

prompt = st.text_input("Input your prompt here")
import time
if prompt:
    start = time.process_time()
    response = retrieval_chain.invoke({"input":prompt})
    print("Response time: ",time.process_time()-start)
    st.write(response['answer'])

    with st.expander("Document Similarity Search"):
        for i, doc in enumerate(response['context']):
            st.write(doc.page_content)
            st.write("-------------------------")


