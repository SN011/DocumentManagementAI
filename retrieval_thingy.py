from tools.imports import *
from dotenv import load_dotenv
import streamlit as st
load_dotenv()
from tools.initialize_groq import init_groq


# Initialize the client and language model
client, llm = init_groq()

# Define the prompt template
prompt = ChatPromptTemplate.from_template(
    """
    Answer the questions based on the provided context only.
    Please provide the most accurate response based on the question.
    YOU ARE A MASTER HVAC TECHNICIAN. YOU MUST BE AUTHORITATIVE AND A BIT SERIOUS IN YOUR RESPONSES. YOU SHOULD BE CONVERSATIONAL BUT NOT TOO PLAYFUL. YOU MUST SAY THAT THE TECHNICIANS WILL DO THE THINGS YOU MENTION. THE TECHNICIANS ARE NOT YOURS. THEY ARE THE TECHNICIANS OF WALTER HVAC SERVICES, CHANTILLY VIRGINIA YOU MUST NEVER SAY "BASED ON THE [whatever context youre given]..." or anything like that. PLEASE DO NOT SAY TO CONSULT A TECHNICIAN, AS YOU ARE THE TECHNICIAN!!!
    <context>
    {context}
    <context>
    Questions: {input}
    """
)

# Function to initialize the vector store with embeddings
def vector_embedding():
    if "vectors" not in st.session_state:
        st.session_state.embeddings = HuggingFaceEmbeddings()
        st.session_state.loader = PyPDFDirectoryLoader("./finetune_docs")
        st.session_state.docs = st.session_state.loader.load()
        st.session_state.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        st.session_state.final_documents = st.session_state.text_splitter.split_documents(st.session_state.docs)
        st.session_state.vectors = FAISS.from_documents(st.session_state.final_documents, st.session_state.embeddings)
        

# Input for user's question
prompt1 = st.text_input("Enter Your Question From Documents:")

# Button to initialize document embeddings
if st.button("Initialize Document Embedding"):
    vector_embedding()
    st.write("Vector Store DB Is Ready")

import time

# Check if user has entered a prompt
if prompt1:
    # Ensure the vector store is ready before processing
    if "vectors" in st.session_state:
        document_chain = create_stuff_documents_chain(llm, prompt)
        retriever = st.session_state.vectors.as_retriever()
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        # Measure response time
        start = time.process_time()
        response = retrieval_chain.invoke({'input': prompt1})
        st.write(f"Response time: {time.process_time() - start} seconds")
        st.write(response['answer'])

        # Display the document similarity search results
        with st.expander("Document Similarity Search"):
            for i, doc in enumerate(response["context"]):
                st.write(doc.page_content)
                st.write("--------------------------------")
    else:
        st.error("Vector Store DB is not ready. Please click 'Initialize Document Embedding' button to create embeddings.")
