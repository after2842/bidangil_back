import sys
import os
import hashlib
import hmac
import base64
import requests
import time

def send_sms(phone_num, nickname, country_code, content):
    timestamp = int(time.time() * 1000)
    timestamp = str(timestamp)
    serviceId = 'ncp:sms:kr:352533455842:bidangil_sms_api'
    access_key = 'ncp_iam_BPAMKR51NO8uI8AuBruS'			# access key id (from portal or Sub Account)
    secret_key = 'ncp_iam_BPKMKR3JIPVfw7c6HIPRcbUmkJja1VzeXN'

                # secret key (from portal or Sub Account)
    secret_key = bytes(secret_key, 'UTF-8')

    method = "POST"
    uri = f"/sms/v2/services/{serviceId}/messages"

    message = method + " " + uri + "\n" + timestamp + "\n"+ access_key
    message = bytes(message, 'UTF-8')
    signingKey = base64.b64encode(hmac.new(secret_key, message, digestmod=hashlib.sha256).digest()).decode('UTF-8')


    url = f'https://sens.apigw.ntruss.com/sms/v2/services/{serviceId}/messages'
    headers = {'x-ncp-apigw-timestamp': timestamp, 'x-ncp-iam-access-key': access_key,'x-ncp-apigw-signature-v2':signingKey, 'Content-Type': 'application/json'}
    body = {
    "type":"SMS",
    "countryCode":country_code,
    "from":"01083413311",
    "content":content,
    "messages":[
        {
            "to":phone_num,

        }
    ],

    }

    response = requests.post(url=url, headers=headers, json=body)
    print(f"res: {response.json()}")
    return response.json()


