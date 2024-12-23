import nest_asyncio
from io import BytesIO
import os
import asyncio
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
import pandas as pd
import requests
import streamlit as st
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_parse import LlamaParse
nest_asyncio.apply()

def verify_gemini_api_key(api_key):
    API_VERSION = 'v1'
    api_url = f"https://generativelanguage.googleapis.com/{API_VERSION}/models?key={api_key}"
    
    try:
        response = requests.get(api_url, headers={'Content-Type': 'application/json'})
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        # If we get here, it means the request was successful
        return True
    
    except requests.exceptions.HTTPError as e:
        
        return False
    
    except requests.exceptions.RequestException as e:
        # For any other request-related exceptions
        raise ValueError(f"An error occurred: {str(e)}")

def verify_gpt_api_key(api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Using a simple request to the models endpoint
    response = requests.get("https://api.openai.com/v1/models", headers=headers)
    
    if response.status_code == 200:
        return True
    elif response.status_code == 401:
        return False
    else:
        print(f"Unexpected status code: {response.status_code}")
        return False

def init_parser(api_key):
    return LlamaParse(api_key=api_key, result_type="markdown", verbose=True)

def generate_text(parser, llm, file_path):
    Settings.chunk_size = 512
    
    if mod == 'Gemini':
        Settings.llm = llm
        Settings.embed_model = "local:BAAI/bge-small-en-v1.5"
    
    documents = parser.load_data(file_path)
    index = VectorStoreIndex.from_documents(documents, transformations=[SentenceSplitter(chunk_size=512)])
    query_engine = index.as_query_engine()
    result = query_engine.query("""
        Could you format this invoice data in a dictionary format that can be used to create a dataframe? 
        Identify the items and their descriptions using logical reasoning. The items and their descriptions (if any) 
        from the invoice data should be put together. If an item has no description, only include the item name.
        Dictionary keys should be: 
        - 'Invoice Number'
        - 'Date'
        - 'Customer Name'
        - 'All items' (a list of strings, each in the format 'Item Name: Description' or just 'Item Name' if there is no description)
        - 'Quantities' (a list of quantities corresponding to each item)
        - 'Amounts' (a list of amounts corresponding to each item)
        - 'Tax' (Total Tax)
        - 'Total Amount'

        Example:
        {
            'Invoice Number': '<invoice number>',
            'Date': '<invoice date>',
            'Customer Name': '<customer name>',
            'All items': ['Item 1: Description 1', 'Item 2'],
            'Quantities': [1, 2],
            'Amounts': [100, 200],
            'Tax' : <Total Tax Amount>
            'Total Amount': <Total Amount>
        }
        """)

    return result['text'] if isinstance(result, dict) and 'text' in result else str(result)

async def process_file(file, parser, llm, upload_directory):
    temp_file_path = os.path.join(upload_directory, file.name)
    with open(temp_file_path, "wb") as f:
        f.write(file.getbuffer())
    
    generated_content = generate_text(parser, llm, temp_file_path)    
    generated_content = re.sub(r"```python\s*|\s*```", "", generated_content)

    os.remove(temp_file_path)
    
    return {
        'File Name': file.name,
        'Content': generated_content
    }

async def process_all_files(files, parser, llm, upload_directory):
    tasks = [process_file(file, parser, llm, upload_directory) for file in files]
    return await asyncio.gather(*tasks)

def main():
    global mod
    mod = None
    validity_model = False
     
    st.header('Invoice Generator') 
    
    # Initialize session state for storing summaries
    if 'data_extracted' not in st.session_state:
        st.session_state.data_extracted = []
          
    with st.sidebar:
        with st.form('OpenAI,Gemini'):
            model = st.radio('Choose Your LLM', ('Gemini','OpenAI'))
            api_key = st.text_input(f'Enter your API key', type="password")
            llamaindex_api_key = st.text_input(f'Enter your llamaParse API key', type="password")
            submitted = st.form_submit_button("Submit")

        if api_key and llamaindex_api_key:
            if model == "Gemini":
                validity_model = verify_gemini_api_key(api_key)
                if validity_model == True:
                    st.write(f"Valid {model} API key")
                else:
                    st.write(f"Invalid {model} API key")
            elif model == "OpenAI":
                validity_model = verify_gpt_api_key(api_key)
                if validity_model == True:
                    st.write(f"Valid {model} API key")
                else:
                    st.write(f"Invalid {model} API key")   
                                     
    if validity_model and llamaindex_api_key:
        if model == 'OpenAI':
            async def setup_OpenAI():
                loop = asyncio.get_event_loop()
                if loop is None:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                os.environ["OPENAI_API_KEY"] = api_key
                llm = ChatOpenAI(model='gpt-4-turbo', temperature=0.6, max_tokens=2000, api_key=api_key)
                print("OpenAI Configured")
                return llm

            llm = asyncio.run(setup_OpenAI())
            mod = 'OpenAI'

        elif model == 'Gemini':
            async def setup_gemini():
                loop = asyncio.get_event_loop()
                if loop is None:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    verbose=True,
                    temperature=0.6,
                    google_api_key=api_key
                )
                print("Gemini Configured")
                return llm

            llm = asyncio.run(setup_gemini())
            mod = 'Gemini'

        parser = init_parser(llamaindex_api_key)
        
        upload_directory = "Saved Files"
        if not os.path.exists(upload_directory):
            os.makedirs(upload_directory)

        uploaded_files = st.file_uploader("Choose files", type=None, accept_multiple_files=True)

        if uploaded_files and st.button("Process Files"):
            if not st.session_state.data_extracted:  
                with st.spinner("Generating invoices for all files..."):
                    st.session_state.data_extracted = asyncio.run(process_all_files(uploaded_files, parser, llm, upload_directory))
            
            if st.session_state.data_extracted:
                for idx, data_extracted in enumerate(st.session_state.data_extracted):
                    st.markdown(f"### File {idx + 1}: {data_extracted['File Name']}")
                    invoice_data = eval(data_extracted['Content'])  # Converting string representation of dict to actual dict
                    rows = []
                    for idx, (item, quantity, amount) in enumerate(zip(
                        invoice_data['All items'], 
                        invoice_data['Quantities'],
                        invoice_data['Amounts']
                    )):
                        rows.append({
                            'Invoice Number': invoice_data['Invoice Number'] if idx == 0 else '',
                            'Date': invoice_data['Date'] if idx == 0 else '',
                            'Customer Name': invoice_data['Customer Name'] if idx == 0 else '',
                            'Item': item,
                            'Quantity': int(quantity),
                            'Tax': '',
                            'Amount': int(amount),
                            'Total amount': ''
                        })
                    
                    total_amount = sum(invoice_data['Amounts'])
                    
                    # Append a separate row for 'Tax' and 'Total Amount'
                    rows.append({
                        'Invoice Number': '',
                        'Date': '',
                        'Customer Name': '',
                        'Item': '',
                        'Quantity': '',
                        'Tax': invoice_data['Tax'],
                        'Amount': total_amount ,
                        'Total amount': invoice_data['Total Amount']
                    })

                    invoice_df = pd.DataFrame(rows)
                    st.table(invoice_df)

                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        invoice_df.to_excel(writer, index=False, sheet_name='Invoices')
                    buffer.seek(0)

                    st.download_button(
                        label=f"Download {data_extracted['File Name']} as Excel",
                        data=buffer,
                        file_name=f"{data_extracted['File Name']}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.markdown("---")  # Separator line

if __name__ == "__main__":
    main()
