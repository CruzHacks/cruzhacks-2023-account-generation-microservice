import http.client
import json
from dotenv import dotenv_values


def get_token():
    config = dotenv_values(".env")

    conn = http.client.HTTPSConnection(config["CONN_URL"])

    payload = f'{{"client_id": "{config["CLIENT_ID"]}","client_secret":"{config["CLIENT_SECRET"]}","audience":"{config["AUD"]}","grant_type":"client_credentials"}}'

    headers = {"content-type": "application/json"}

    conn.request("POST", "/oauth/token", payload, headers)

    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))

    return data["access_token"]


print(get_token())
