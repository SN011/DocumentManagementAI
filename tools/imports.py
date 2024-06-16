import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import googleapiclient.errors
from googleapiclient.errors import HttpError
import time
from langchain.tools import BaseTool
import re
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from tools.initialize_groq import *

#_______________________________________
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, Extra
#________________________________________
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
#__________________________________________
from langchain.tools import BaseTool
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import googleapiclient
import google.auth.exceptions

import os
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, Extra