import base64
import json
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


def get_attachments(service, user_id, message_id, file_types=['.csv', '.xlsx']):
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
            data_stats_summary(file_path)

            # Call AWS Bedrock Claude 3 to summarize
            

            # Delete the file
            os.remove(file_path)

def data_stats_summary(file_name):
    if file_name.endswith('.csv'):
        df = pd.read_csv(file_name)
    elif file_name.endswith('.xlsx'):
        df = pd.read_excel(file_name)
    summary = df.describe()
    print(summary)

    # if df has more than 2 rows, print the first 2 rows
    if len(df) > 2:
        print("First 2 rows:")
        print(df.head(2))

    return summary            



# def summarize_data(df):
#     # Serialize DataFrame to JSON 
#     data = json.dumps(df.to_dict())

#     # Initialize Bedrock client
#     client = BedrockRuntimeClient(region_name="region-name")

#     # Invoke Claude model
#     response = client.send(
#         InvokeModelCommand(
#         model_id="anthropic.claude-3-opus-20231101-v1:0", 
#         body=data
#         )
#     )
#     result = response.result["text/markdown"]
#     print(f"Result from LLM: {result}")
#     # Return summary in Markdown format
#     return result 


# main logic 
service = gmail_authenticate()
messages_ids = list_messages(service, 'me')
print("Email Message IDs that have attachment:", messages_ids)
for message_id in messages_ids:
    get_attachments(service, 'me', message_id["id"])
