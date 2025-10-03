import os
import pickle
import re
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient.errors as errors
from base64 import urlsafe_b64decode

# define path
path = '/storage2/common/get-buoy-data/'

# define scope for permissions on gmail account
#SCOPES = ['https://mail.google.com/'] # full access
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly'] # read only
our_email = 'cabp.mcgill@gmail.com'

# read file that has info on when was this script last executed
if os.path.isfile(path + 'last_access'):
    with open(path + 'last_access', "r") as f:
        last_access = str(f.read())
    f.close()
else:
    last_access = "1970/01/01 00:00:00"

last_timestamp = int(datetime(int(last_access[0:4]), int(last_access[5:7]),
                              int(last_access[8:10]), int(last_access[11:13]),
                              int(last_access[14:16]), int(last_access[17:19])).timestamp())
# time of this access to gmail account
access_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

# function to authenticate for gmail access
# copied from https://thepythoncode.com/article/use-gmail-api-in-python
def gmail_authenticate(path):
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists(path + "token.pickle"):
        with open(path + "token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(path + 'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open(path + "token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# function search messages with specific attributes
# copied from https://thepythoncode.com/article/use-gmail-api-in-python
def search_messages(service, query):
    result = service.users().messages().list(userId='me',q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages

# function to create a label from each message
# only used to create the filename for now
def label_messages(service, msg_id):
    try:
        messageheader= service.users().messages().get(userId="me", id=msg_id['id'], format="full", metadataHeaders=None).execute()
        headers = messageheader["payload"]["headers"]
        subject = [i['value'] for i in headers if i["name"]=="Subject"][0]
        label = re.sub("[^0-9]", "", subject)
    except errors.HttpError:
        print("HttpError, skipping message with id: " + str(msg_id['id']))
        label = "skip"
    return label

# function to download attachements
# copied and slightly modified from https://stackoverflow.com/a/27335699
def GetAttachments(service, msg_id, path):
    try:
        message = service.users().messages().get(userId="me", id=msg_id['id']).execute()
        for part in message['payload']['parts']:
            if part['filename']:
                filename = part['filename']
                if os.path.isfile(path + filename):
                    pass
                else:
                    if 'data' in part['body']:
                        data = part['body']['data']
                    else:
                        att_id = part['body']['attachmentId']
                        att = service.users().messages().attachments().get(userId="me", messageId=msg_id['id'], id=att_id).execute()
                        data = att['data']
                    file_data = urlsafe_b64decode(data.encode('UTF-8'))
                    with open(path + filename, 'wb') as f:
                        f.write(file_data)
    except errors.HttpError:
        print("HttpError, skipping message with id: " + str(msg_id['id']))
    return

# authenticate with gmail to access account
service = gmail_authenticate(path)

# define query to search for messages
# it needs to be from sbd.iridium.com
# we want it to have been received after our last access to the the account
# and it needs to have an attachement
query = f'from:sbd.iridium.com after:{last_timestamp} has:attachment'
# get the IDs of the messages that fit the query
messages = search_messages(service, query)
# if messages that meet the requirements exist,
# loop through all those messages, download and save attachments
if len(messages) > 0:
    print("Downloading " + str(len(messages)) + " new messages...")
    for msg_id in messages:
        label = label_messages(service, msg_id)
        if label != "skip":
            if not os.path.exists(path + label):
                os.makedirs(path + label)
            GetAttachments(service, msg_id, path + label + '/')
else:
    print("No new messages since " + str(last_access))

# save access time
with open(path + "last_access", "w") as f:
    f.write(str(access_time))
f.close()
