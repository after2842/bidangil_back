import requests

date = 'latest'
apiVersion = 'v1'
endpoint = 'currencies/usd'

def get_exchange_rate():
    url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/{apiVersion}/{endpoint}.json"
    response = requests.get(url = url)
    data = response.json()
    krw_per_dollar = data['usd']['krw']
    exchange_date = data['date']

    return krw_per_dollar
        