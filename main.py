import base64
import json
import boto3
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pandas as pd
import os
# from aws_bedrock_runtime import BedrockRuntimeClient
# from aws_bedrock_runtime.model import InvokeModelCommand



SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def gmail_authenticate():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    # Print the redirect URI 
    print("redirect URI:", flow.authorization_url()) 
    creds = flow.run_local_server(port=0)
    service = build('gmail', 'v1', credentials=creds)
    return service



def list_messages(service, user_id):
    results = service.users().messages().list(userId=user_id, q="has:attachment").execute()
    return results.get('messages', [])


def process_attachments(service, user_id, message_id, file_types=['.csv', '.xlsx']):
    message = service.users().messages().get(userId=user_id, id=message_id).execute()
    for part in message['payload']['parts']:
        file_name = part['filename']
        if any(file_name.endswith(ext) for ext in file_types):
            attachment_id = part['body']['attachmentId']
            attachment = service.users().messages().attachments().get(userId=user_id, messageId=message_id, id=attachment_id).execute()
            data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
            
            # Save the file temporarily, could specify a path or use tempfile for more robust handling
            file_path = f"./{file_name}"
            with open(file_path, "wb") as f:
                f.write(data)
            
            print(f"Downloaded {file_name}")
            # Call the summarize function
            stats, data = data_stats(file_path)
            # convert data to str using json

            # Call AWS Bedrock Claude to summarize
            summarize_data(data)

            # Delete the file
            os.remove(file_path)


"""
Function to calculate statistics and retrieve data from a CSV or Excel file.

Args:
    file_name (str): The path to the CSV or Excel file. The file extension 
        must be either '.csv' or '.xlsx'.

Returns: 
    stats (pandas DataFrame): The descriptive statistics of the DataFrame.
    data (str): The DataFrame converted to a JSON string.
"""
def data_stats(file_name): 
    if file_name.endswith('.csv'):
        df = pd.read_csv(file_name)
    elif file_name.endswith('.xlsx'):
        df = pd.read_excel(file_name)
    stats = df.describe()
    print(stats)

    # if df has more than 2 rows, print the first 2 rows
    if len(df) > 2:
        print("First 2 rows:")
        print(df.head(2))

    # convert df to json
    data: str = json.dumps(df.to_dict())
    return stats, data



def summarize_data(data):
    
    # access_key = 'your-access-key-id'
    # secret_key = 'your-secret-access-key'

    # session = boto3.Session(
    #    aws_access_key_id=access_key,
    #    aws_secret_access_key=secret_key,
    #    region_name='us-east-1'
    # )
    # bedrock_client = session.client('bedrock-runtime')

    bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

    prompt: str = f"\n\nHuman: Summarize the following data: <data> {data} </data> \n\nAssistant:"

    # Print the first 100 characters of the prompt
    print(f"\n\nInvoking Bedrock with prompt: {prompt[:100]} ... ... {prompt[-20:]}\nResponse from Bedrock\n")

    body = json.dumps({
        'prompt': prompt,
        'max_tokens_to_sample': 4000
    })
                    
    response = bedrock_runtime.invoke_model_with_response_stream(
        modelId='anthropic.claude-v2', 
        body=body
    )
        
    stream = response.get('body')
    if stream:
        for event in stream:
            chunk = event.get('chunk')
            if chunk:
                res = json.loads(chunk.get('bytes').decode())
                print(res["completion"], end=" ")


# main logic 
service = gmail_authenticate()
messages_ids = list_messages(service, 'me')
# print("Email Message IDs that have attachment:", messages_ids)
for message_id in messages_ids:
    process_attachments(service, 'me', message_id["id"])
