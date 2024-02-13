import os
import time
import requests
from dotenv import load_dotenv
from threading import Thread
from google.cloud import storage
from flask import Flask, jsonify
import smtplib
import os

load_dotenv()


# Constants
TOKEN = None
SITE_ID = os.getenv('SITE_ID')
TENANT_ID = os.getenv('TENANT_ID')
bucket_name = os.getenv('BUCKET_NAME')
URL = f'https://graph.microsoft.com/v1.0/sites/{SITE_ID}/drive/root/children'

# Initialize a GCS client
storage_client = storage.Client()
bucket = storage_client.get_bucket(bucket_name)


def fetch_token():
    global TOKEN
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"
    payload = {
        'grant_type': 'client_credentials',
        'client_id': os.getenv('CLIENTID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'resource': os.getenv('RESOURCE')
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        json_response = response.json()
        access_token = json_response['access_token']
        # Store the access token in a secure place
        
        TOKEN = access_token
        return TOKEN
    else:
        print(f"Failed to fetch token, status code: {response.status_code}")

# scheduler = BlockingScheduler()
# scheduler.add_job(fetch_token, 'interval', minutes=60) 


# Below Code Provides Sol^2 :  Periodic Check to see if the new files are added and if uploads them to GCS Bucket

def make_requests():
    global TOKEN
    while True:
        # Make the GET request
        # Headers
        headers = {
            'Authorization': f'Bearer {TOKEN}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        response = requests.get(URL, headers=headers)
        # print(response.json())
        if response.status_code == 200:
            data = response.json()
            for item in data['value']:

                # If the file is new  -- in set() # -- RETIRED
                # if item['name'] not in file_names:

                # If the file is new in bucket()
                blob = bucket.blob(item['name'])
                if not blob.exists():
                    # print(f'New file found: {item["name"]}')   # -- TESTING LOCALLY
                

                    if 'file' in item and '@microsoft.graph.downloadUrl' in item:
                        print(f'New file found: {item["name"]}')
                        print(item)

                        # # Download the file
                        download_url = item['@microsoft.graph.downloadUrl']
                        file_response = requests.get(download_url)

                        # Save the file
                        with open(item['name'], 'wb') as f:
                            f.write(file_response.content)

                        # Upload the file to GCS
                        # blob = bucket.blob(item['name'])  # -- RETIRED

                        blob.upload_from_filename(item['name'])
                        # print(f'Uploaded {item["name"]} to {bucket_name}')
                        
                        os.remove(item['name'])
                        
                # print(item['name'])    # -- TESTING LOCALLY

        elif response.status_code == 401:
            fetch_token()
        else:
            print(f'Request failed with status code {response.status_code}')
        time.sleep(1)

fetch_token()  # Fetch the token before starting the loop

# Start the background task
thread = Thread(target=make_requests)
thread.start()

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/send_email', methods=['GET'])
def send_email():
    email = "vaibhav.shukla123.gcp0@gmail.com"

    text = "Subject: sub \n\n Email Sending from Cloud Run"
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    server.login(email, "pzwclgdafacagsuh")
    server.sendmail(email, "vaibhavshukla.try@gmail.com", text)

    print("Email sent succefully")
    return jsonify({"message": "Email sent successfully"})


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)



