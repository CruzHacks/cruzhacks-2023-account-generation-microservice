import http.client
import json
from typing import List
from dotenv import dotenv_values
import requests
import time
import csv


def get_management_token():
    config = dotenv_values(".env")

    conn = http.client.HTTPSConnection(config["CONN_URL"])

    payload = (
        '{"client_id":'
        f' "{config["CLIENT_ID"]}","client_secret":"{config["CLIENT_SECRET"]}","audience":"{config["AUD"]}","grant_type":"client_credentials"}}'
    )

    headers = {"content-type": "application/json"}

    conn.request("POST", "/oauth/token", payload, headers)

    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))

    return data["access_token"]


def get_admin_token():
    config = dotenv_values(".env")
    url = "https://" + config["CONN_URL"] + "/oauth/token"
    payload = json.dumps(
        {
            "client_id": config["ADMIN_CLIENT_ID"],
            "client_secret": config["ADMIN_CLIENT_SECRET"],
            "audience": config["ADMIN_AUDIENCE"],
            "grant_type": "client_credentials",
        }
    )

    headers = {"content-type": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload).json()

    return response["access_token"]


def generate_password(
    password_length=15, upper_chars=1, lower_chars=1, digit_chars=1, special_chars=1
):
    import string
    import secrets

    alphabet = string.digits + string.ascii_letters + "!@#$%^&*()_-+=[]{}:;<>?"

    password = ""
    while True:
        password = "".join(secrets.choice(alphabet) for i in range(password_length))
        upper_count = 0
        lower_count = 0
        special_count = 0
        digit_count = 0

        for character in password:
            if character.isupper():
                upper_count += 1
            elif character.islower():
                lower_count += 1
            elif character.isdigit():
                digit_count += 1
            elif character in string.punctuation:
                special_count += 1

        if (
            upper_count >= upper_chars
            and lower_count >= lower_chars
            and special_count >= special_chars
            and digit_count >= digit_chars
        ):
            break

    return password


def get_users_from_csv(csv_file: str):
    import csv

    user_list = []
    with open(csv_file, newline="") as users:
        reader = csv.DictReader(users)
        for user in reader:
            user_list.append(user)

    return user_list


def create_users_json(token: str, accounts: List[dict], connection_id: str):
    accounts_list = []
    for account in accounts:
        user_obj = {
            "email": account["Email"],
            "email_verified": True,
            "given_name": account["First Name"],
            "family_name": account["Last Name"],
            "app_metadata": {"roles": ["Hacker"]},
        }

        accounts_list.append(user_obj)

    with open("accounts.json", "w", encoding="utf-8") as f:
        json.dump(accounts_list, f, ensure_ascii=False, indent=2)

    config = dotenv_values(".env")

    url = "https://" + config["CONN_URL"] + "/api/v2/jobs/users-imports"
    payload = {"connection_id": connection_id}
    files = [
        ("users", ("file", open("accounts.json", "rb"), "application/octet-stream"))
    ]
    headers = {"authorization": f"Bearer {token}"}

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    return response.text


def get_auth0_users(token: str, page: int):
    config = dotenv_values(".env")
    url = "https://" + config["CONN_URL"] + "/api/v2/users"
    headers = {"authorization": f"Bearer {token}"}
    data = {"q": {"app_metadata.roles: Hacker"}, "page": page}
    users = requests.request("GET", url, headers=headers, params=data).json()
    userList = []

    for user in users:
        userList.append(
            {
                "auth0ID": user["user_id"],
                "email": user["email"],
                "firstName": user["given_name"],
                "lastName": user["family_name"],
            }
        )

    return userList


def attach_role(token: str, users: List[dict], role: str):
    config = dotenv_values(".env")
    conn = http.client.HTTPSConnection(config["CONN_URL"])
    user_ids = [user["auth0ID"] for user in users]
    print(user_ids)
    payload = f'{{"users": {json.dumps(user_ids)}}}'

    headers = {"Authorization": f"Bearer {token}", "content-type": "application/json"}

    conn.request("POST", f"/api/v2/roles/{role}/users", payload, headers)

    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    return data


def generate_accounts(admin_token: str, userList: List[dict]):
    config = dotenv_values(".env")
    url = config["API_ENDPOINT"] + "/hacker/bulkCreateHackers"
    payload = json.dumps({"users": userList})
    headers = {
        "authorization": f"Bearer {admin_token}",
        "content-type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text


def generate_email_list_data(management_token: str, userList: List[dict]):
    config = dotenv_values(".env")
    url = "https://" + config["CONN_URL"] + "/api/v2/tickets/password-change"
    email_list_data = []
    for user in userList:
        payload = json.dumps(
            {
                "client_id": config["ADMIN_CLIENT_ID"],
                "user_id": user["auth0ID"],
            }
        )
        headers = {
            "authorization": f"Bearer {management_token}",
            "content-type": "application/json",
        }
        response = requests.request("POST", url, headers=headers, data=payload).json()
        user_email_data = {
            "First Name": user["firstName"],
            "Last Name": user["lastName"],
            "Email Address": user["email"],
            "Password Reset": response["ticket"],
        }
        email_list_data.append(user_email_data)
        time.sleep(1)

    return response["ticket"]


def generate_password_reset_link(management_token: str, email: str):
    config = dotenv_values(".env")
    url = "https://" + config["CONN_URL"] + "/api/v2/users-by-email"
    headers = {"authorization": f"Bearer {token}"}
    data = {"email": email}
    res = requests.request("GET", url, headers=headers, params=data).json()
    auth0ID = res[0]["user_id"]

    url = "https://" + config["CONN_URL"] + "/api/v2/tickets/password-change"
    payload = json.dumps(
        {
            "client_id": config["ADMIN_CLIENT_ID"],
            "user_id": auth0ID,
        }
    )
    headers = {
        "authorization": f"Bearer {management_token}",
        "content-type": "application/json",
    }
    response = requests.request("POST", url, headers=headers, data=payload).json()
    print(response["ticket"])


token = get_management_token()
admin_token = get_admin_token()

generate_password_reset_link(token, "fakeemail@gmail.com")
