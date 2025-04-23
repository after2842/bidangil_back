import requests
import json
def get_secret_key():
  url = "https://apis.fedex.com/oauth/token"

  headers = {"Content-Type":"application/x-www-form-urlencoded"}
  payload = {"grant_type":"client_credentials","client_id":"l7518a7f8fd5fd4ed9ad571abbc0a47ed9", "client_secret":"b7e616876c5e401688112f4a11598458"}
  response = requests.post(url = url, headers=headers, data = payload)
  response_data = response.json()
  return response_data['access_token']


def get_fedex_status(tracking_num, secret):
    url = "https://apis.fedex.com/track/v1/trackingnumbers"

    payload = {
        "includeDetailedScans": False,
        "trackingInfo": [
            {
                "trackingNumberInfo": {
                    "trackingNumber": tracking_num
                }
            }
        ]
    }
    headers = {
        'Content-Type': "application/json",
        'X-locale': "en_US",
        'Authorization': f"Bearer {secret}"
        }

    response = requests.post(url, data=json.dumps(payload), headers=headers)

    tracking_info = response.json()
    try:
        if 'completeTrackResults' in tracking_info['output']:
            print('complete status')
            tracking_result = tracking_info['output']['completeTrackResults'][0]['trackResults'][0].get('latestStatusDetail')
            return tracking_result
            
        else:
            trackresults =  tracking_info['output'][0]['trackResults'][0].get('latestStatusDetail')
            print('update track')
            return trackresults
    except Exception as e:
        print(e,'trackinginfo failed')
        return None
