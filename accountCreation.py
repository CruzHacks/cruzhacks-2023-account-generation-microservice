import http.client
import json
from typing import List
from dotenv import dotenv_values
import requests


def get_token():
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
        password = generate_password()
        user_obj = {
            "email": account["Email"],
            "email_verified": True,
            "given_name": account["First Name"],
            "family_name": account["Last Name"],
            "password": password,
            "app_metadata": {"roles": ["User"]},
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


def attach_role(token: str, users: List[str], role: str):
    config = dotenv_values(".env")

    conn = http.client.HTTPSConnection(config["CONN_URL"])

    payload = f'{{"users": {json.dumps(users)}}}'

    print(payload)

    headers = {"Authorization": f"Bearer {token}", "content-type": "application/json"}

    conn.request("POST", f"/api/v2/roles/{role}/users", payload, headers)

    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    return data


token = get_token()

# print(attach_role(token, ["auth0|639a1e85a18a9231c701d5e0"], "rol_pXJ21VmBuPwJQjyE"))

user_list = get_users_from_csv("TestData.csv")
# print(create_account(token, user_list[0], generate_password()))
print(create_users_json(token, user_list, "con_0blCoUfG5H8M1U4z"))
# account_ids = []
# for user in user_list:
#     token = get_token()
#     password = generate_password()
#     data = create_account(token, user, password)
#     try:
#         account_ids.append(data["user_id"])
#     except KeyError:
#         print("Unable to Create Account")
