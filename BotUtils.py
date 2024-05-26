from langchain.agents import load_tools, create_structured_chat_agent, AgentExecutor
from groq import Groq
import string
import os
import random
from langchain_groq import ChatGroq
from langchain_core.prompts import (
    ChatPromptTemplate, ChatMessagePromptTemplate, HumanMessagePromptTemplate,
    SystemMessagePromptTemplate, PromptTemplate, MessagesPlaceholder
)
import typing
import langchain_core
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.tools.retriever import create_retriever_tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.tools.tavily_search import TavilySearchResults
import re

class BotBase:
    def __init__(self, llm: ChatGroq):
        self.llm = llm

    def initialize(self):
        raise NotImplementedError("Subclasses should implement this method")

    def invoke(self, query):
        raise NotImplementedError("Subclasses should implement this method")


class WebSearchAgent(BotBase):
    def __init__(self, llm: ChatGroq):
        super().__init__(llm)
        self.vector = None
        self.retriever = None

    def initialize(self):
        self.create_prompt()
        self.create_vector()
        self.create_chains()

    def create_prompt(self):
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a world class technical documentation writer"),
            ("user", "{input}")
        ])
        self.output_parser = StrOutputParser()

    def create_vector(self):
        loader = WebBaseLoader("https://docs.smith.langchain.com/overview")
        docs = loader.load()
        embeddings = HuggingFaceEmbeddings()
        text_splitter = RecursiveCharacterTextSplitter()
        documents = text_splitter.split_documents(docs)
        self.vector = FAISS.from_documents(documents, embeddings)

    def create_chains(self):
        retriever = self.vector.as_retriever()
        self.retrieval_chain = create_retrieval_chain(retriever, self.create_document_chain())

    def create_document_chain(self):
        prompt = ChatPromptTemplate.from_template("""Answer the following question based only on the provided context:

        {context}

        Question: {input}""")
        return create_stuff_documents_chain(self.llm, prompt)

    def invoke(self, query):
        response = self.retrieval_chain.invoke({"input": query})
        return response["answer"]


class QuoteBot(BotBase):
    def __init__(self, client: Groq, llm: ChatGroq):
        super().__init__(llm)
        self.client = client
        self.system_msg = """
                You are an expert at questioning the client about their renovation or construction project quote.
                Please keep in mind all of these things when asking questions: ask the user specific info needed for the quote, such as:

                    1.Property Details:
                    Address and location of the property.
                    Type of property (e.g., residential, commercial).
                    Age and current condition of the property.
                    Square footage of the area to be renovated.
                    2.Scope of the Project:
                    Detailed description of the renovation work required.
                    Specific areas or rooms that need renovation.
                    Desired changes and additions (e.g., new rooms, extensions, wall removal).
                    Level of finishes desired (standard, premium, luxury).
                    3.Design Preferences:
                    Style or theme of the renovation (modern, traditional, industrial, etc.).
                    Color schemes and material preferences.
                    Any specific fixtures or features desired (e.g., type of flooring, lighting fixtures).
                    4.Budget:
                    Your budget range for the project.
                    Any flexibility within the budget.
                    5.Timeline:
                    Desired start date and completion date.
                    Any constraints or deadlines (e.g., events planned at the property).
                    Legal and Compliance Information:
                    Information on any permits or approvals already obtained.
                    Any restrictions or caveats affecting the property.
                    6.Utility Modifications:
                    Changes or improvements to electrical, plumbing, or HVAC systems.
                    Details of any provisions for appliances or systems (e.g., energy-efficient or smart home features).
                    7.Access & Logistics:
                    Access requirements for renovation or construction work (e.g., elevator access, restricted hours).
                    Logistic considerations necessary for the project (e.g., space for storing materials, parking for construction vehicles).
                    8.Special Requirements:
                    Access provisions for renovations or construction work done on the property.
                    Special considerations or instructions (e.g., conserving existing architectural features).
                    What specific materials they are looking at.
                    Information about other construction or renovation projects completed on the property.
                    IMPORTANT!: Make sure you get clear answers from the user that can actually be used for making the quote, and if you are not provided a clear answer ask to clarify, and restate the question and explain what it means.
                    IMPORTANT!: Ask each question that you have ONE BY ONE

                    IMPORTANT!: WHEN YOU HAVE ALL THE INFORMATION, JUST SAY 'hehehe' at the end.
                """
        self.chat_history = []

    def initialize(self):
        self.start_conversation()

    def start_conversation(self):
        while True:
            client_req = str(input())
            response = self.ask_question(client_req)
            self.chat_history.append(response)
            if 'hehehe' in response.lower():
                break

    def ask_question(self, client_req):
        quotebot = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.system_msg},
                {"role": "user", "content": f"{client_req} Chat History for your own context and info - DONT ASK A QUESTION IF THE ANSWER IS ALREADY IN CHAT HISTORY: {self.chat_history}"}
            ],
            model="llama3-70b-8192",
        )
        return quotebot.choices[0].message.content

    def create_material_plan(self):
        consultors_list = []
        consultationbot = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.system_msg},
                {"role": "user", "content": f"You are a professional renovation consultant. Based on the chat history, create a streamlined material plan for the user's quote request, choosing what materials to use, and how much would be used and where. MAKE SURE TO BE VERY SPECIFIC in what materials you will use and how much. ALSO MAKE SURE TO PROVIDE A BLURB AT THE START OF THE RESPONSE And THEN A MATERIAL LIST AND HOW MUCH YOU WILL NEED. DO NOT LIST PRICES JUST LIST MATERIALS NEEDED AND HOW MUCH OF THAT MATERIAL. Here is the chat history: {self.chat_history}"}
            ],
            model="llama3-70b-8192",
        )
        consoltation_output = consultationbot.choices[0].message.content
        consultors_list.append(consoltation_output)
        return consoltation_output

    def create_quote(self, consoltation_output):
        quotebot = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant INCLUDE ADDRESS OF CLIENT AT ALL TIMES!!!! IT IS IN CHAT HISTORY!! INCLUDE ADDRESS OF CLIENT AT ALL TIMES!!!! IT IS IN CHAT HISTORY!! INCLUDE ADDRESS OF CLIENT AT ALL TIMES!!!! IT IS IN CHAT HISTORY!!"},
                {"role": "user", "content": f"Based on the chat history as well as the consultors list of materials, you must put all the required information for the quote (along with location of property) into a streamlined format so that a web search query can be formed for it. Your response must be well-formed and include all details EVEN THE EXPLICIT ADDRESS!!. List every item explicitly. INCLUDE ADDRESS OF CLIENT AT ALL TIMES!!!! IT IS IN CHAT HISTORY!! Chat History for your own context and info: [{self.chat_history}][Consultors List: {consoltation_output}]"}
            ],
            model="llama3-70b-8192",
        )
        streamlined_output = quotebot.choices[0].message.content

        agent_executor = initialize_web_search_agent(llm=self.llm)
        output = agent_executor.invoke({
            "input": f"Given the chat history --> {streamlined_output} <-- AS WELL AS THE CONSULTANT'S INFORMATION --> {consoltation_output} --> look for labor and material costs for whatever the user asked for in the AREA NEAR ADDRESS OF USERS PROPERTY. maybe also use the costs of houses or properties very near to that location to decide on the cost. BE VERY SPECIFIC. LOTS OF NUMBERS. Also for material costs only use the consoltation_output, and search up the materials individually to find the price."
        })

        refined_output = str(output["output"])
        refined_output = refined_output[refined_output.find('"')+1:refined_output.rfind('"')-1]

        # Original string with escaped characters and formatting issues
        original_string = fr''' {refined_output} '''

        # Clean up the string
        cleaned_string = original_string.replace('\\n', '\n').replace('\\t', '\t').replace(r"\'", "'")

        # Optional: further beautify by stripping leading/trailing whitespace and fixing indentation
        cleaned_string = re.sub(r'\n\s*', '\n', cleaned_string)  # Remove spaces following new lines
        cleaned_string = cleaned_string.strip()  # Remove the leading and trailing whitespace
        refined_output = cleaned_string
        print(cleaned_string)

        quotebot2 = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert in PREPARING A REAL ESTATE QUOTE IN PROPER FORMAT from ONLY what is in the user's request, given a web search synthesis as one input and user's request as another input.
                        YOU ARE TO FOLLOW THIS TEMPLATE AT ALL TIMES - EXACTLY ONLY ONLY ONLY ONLY ONLY ONLY ONLY ONLY!!!!!!! IN THIS FORMAT - OR ELSE YOU WILL BE SAD FOR THE REST OF YOUR LIFE 
                            ALL COMPONENTS AND ITEMIZED ITEMS SHALL BE LEFT EXACTLY AS IN INPUT (IMPORTANT: ITEMIZED COSTS IN THE INPUT SHALL BE LEFT ALONE; DO NOT LUMP THEM IN MISCELLANEOUS): 
                            **Project Overview:**
    - Project Description: [Brief description of the project scope and objectives]
    - Length of Time for Project [User's desire for how much time he wants to do renovations]

    **Cost Breakdown:**

    1. **Labor Costs:**
    - Total Labor Cost: $[Total Labor Cost]

    2. **Material Costs:**
    - Total Material Cost: $[Total Material Cost]
    - Itemized Costs:
        + [Material 1 with any lengths and areas]: $[Cost]
        + [Material 2 with any lengths and areas]: $[Cost]
        + [Material 3 with any lengths and areas]: $[Cost]
        + [... ALL OTHER MATERIALS MUST FOLLOW THIS FORMAT. THE COST IS THE ONLY THING AFTER COLON!!!]

    **Total Estimated Cost:**
    - Total Cost of Labor: $[Total Labor Cost]
    - Total Cost of Materials: $[Total Material Cost]
    - **Grand Total: $[Total Estimated Cost]**

    **Payment Terms:**
    - Deposit Required: [Percentage]
    - Payment Schedule: Monthly payments of [amount] for [number] months
    - Final Payment Due: [Date or condition upon which the final payment is due]
    """
                },
                {
                    "role": "user",
                    "content": f"Based on the input, which is <<<{refined_output}>>> you must parse the input for the renovation quote so that your response talks about ONLY the stuff relevant to the user's quote request. Omit the 'average' costs and 'sources'. IMPORTANT: GIVE AN EXACT AMOUNT FOR MATERIAL VALUE & LABOR COST: NO RANGES ! PICK MAX. User's request for your own context and info: {output}"
                }
            ],
            model="llama3-70b-8192",
        )
        output2 = quotebot2.choices[0].message.content
        print(output2)

        quote_dict_corrected = QuoteParser.parse_quote(output2)
        corrector = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in correcting an input. YOU MUST START THE RESPONSE WITH 'RENOVATION QUOTE DOCUMENT' heading. ADDRESS MUST BE INCLUDED IT WILL BE THERE IN THE CONTEXT GIVEN TO YOU! YOU MUST INCLUDE ALLLLLLLLLLLLLLLLLLLLLLL ITEMIZED COSTS NO MATTER HOWEVER LONG THE LIST OF ITEMIZED COSTS IS !!!! THIS IS A RENOVATION QUOTE AND WE NEED TO KNOW EVERY SINGLE DAMN COST!!!!"
                },
                {
                    "role": "user",
                    "content": f"Based on the input, which is <<<{output2}>>>, you must parse the input from the renovation quote and REPLACE AS IT IS the total values for the following categories: LABOR COSTS: ${quote_dict_corrected['labor_cost']}, MATERIAL COSTS: ${quote_dict_corrected['total_material_cost']}, and TOTAL ESTIMATED COSTS: ${quote_dict_corrected['total_estimated_cost']}, and DEPOSIT: {quote_dict_corrected['payment_terms']['deposit_required']} MONTHLY PAYMENT {quote_dict_corrected['payment_terms']['payment_schedule']}."
                }
            ],
            model="llama3-70b-8192",
        )
        corrector_output = corrector.choices[0].message.content
        print('CORRECTED MATH OUTPUT\n\n\n\n\n\n', corrector_output)
        return corrector_output

from contextlib import contextmanager
class CtxMgr:
    @contextmanager
    def temporary_temperature(self, llm: ChatGroq, new_temp: float):
        original_temp = llm.temperature  # Store the original temperature
        llm.temperature = new_temp  # Set the temperature to the temporary value
        try:
            yield  # Pause here and allow the `with` block to execute
        finally:
            llm.temperature = original_temp


class QuoteParser:
    @staticmethod
    def parse_quote(quote_str):
        quote_details = {
            "project_description": "",
            "project_duration": "",
            "labor_cost": 0,
            "material_costs": {},
            "total_material_cost": 0,
            "total_estimated_cost": 0,
            "payment_terms": {}
        }

        # Extracting Project Details
        description_match = re.search(r"Project Description: (.+)", quote_str)
        duration_match = re.search(r"Length of Time for Project: (.+)", quote_str)
        if description_match:
            quote_details["project_description"] = description_match.group(1)
        if duration_match:
            quote_details["project_duration"] = duration_match.group(1)

        # Extract labor cost
        labor_cost_match = re.search(r"Total Labor Cost: \$(\d+[\d,]*)", quote_str)
        if labor_cost_match:
            quote_details["labor_cost"] = int(labor_cost_match.group(1).replace(',', ''))

        # Extracting and Summing Material Costs
        material_cost_matches = re.finditer(r"\+\s*(.*?):\s*\$(\d+[\d,]*)", quote_str)
        for match in material_cost_matches:
            item = match.group(1).strip()
            cost = int(match.group(2).replace(',', ''))
            quote_details["material_costs"][item] = cost

        quote_details["total_material_cost"] = sum(quote_details["material_costs"].values())

        # Calculating Total Estimated Cost
        quote_details["total_estimated_cost"] = quote_details["labor_cost"] + quote_details["total_material_cost"]

        # Extracting Payment Terms
        deposit_match = re.search(r"Deposit Required: (\d+)%", quote_str)
        #payment_schedule_match = re.search(r"Payment Schedule: Monthly payments of \$(\d+[\d,]*) for (\d+) months", quote_str)
        payment_schedule_match = re.search(r"Payment Schedule: Monthly payments of \$([\d,]+(?:\.\d{1,2})?) for (\d+) months", quote_str)
        final_payment_due_match = re.search(r"Final Payment Due: (.+)", quote_str)
        tmp = None
        if deposit_match:
            deposit_percentage = int(deposit_match.group(1))
            deposit_amount = (quote_details["total_estimated_cost"] * deposit_percentage) / 100
            quote_details["payment_terms"]["deposit_required"] = f"{deposit_percentage}% (${deposit_amount:.2f})"
            tmp = deposit_amount
        if payment_schedule_match:
            number_of_months = int(re.search(r"for (\d+) months", quote_str).group(1)) if re.search(r"for (\d+) months", quote_str) else 6  # Default to 6 if not found
            monthly_payment = (quote_details["total_estimated_cost"] - tmp) / number_of_months
            quote_details["payment_terms"]["payment_schedule"] = f"Monthly payments of ${int(monthly_payment):,} for {number_of_months} months"

        if final_payment_due_match:
            quote_details["payment_terms"]["final_payment_due"] = final_payment_due_match.group(1)

        return quote_details


def initialize_web_search_agent(llm: ChatGroq):
    agent = WebSearchAgent(llm)
    agent.initialize()
    return agent


def initialize_quote_bot(client: Groq, llm: ChatGroq):
    quote_bot = QuoteBot(client, llm)
    quote_bot.initialize()
    consoltation_output = quote_bot.create_material_plan()
    return quote_bot.create_quote(consoltation_output)



def main():
    llm = ChatGroq()
    client = Groq()

    # Initialize agents
    web_search_agent = initialize_web_search_agent(llm)
    quote_output = initialize_quote_bot(client, llm)

    print(quote_output)


if __name__ == "__main__":
    main()
