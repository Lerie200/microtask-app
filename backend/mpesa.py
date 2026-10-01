import os
import base64
import requests
from datetime import datetime

DARAJA_BASE_URL = "https://sandbox.safaricom.co.ke"  # sandbox; switch to api.safaricom.co.ke for production

CONSUMER_KEY = os.getenv("DARAJA_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("DARAJA_CONSUMER_SECRET")
SHORTCODE = os.getenv("DARAJA_SHORTCODE")
PASSKEY = os.getenv("DARAJA_PASSKEY")
CALLBACK_URL = os.getenv("DARAJA_CALLBACK_URL")


def get_access_token():
    """Authenticate with Daraja and return a short-lived OAuth access token."""
    url = f"{DARAJA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(CONSUMER_KEY, CONSUMER_SECRET))
    response.raise_for_status()
    return response.json()["access_token"]


def format_phone_for_mpesa(phone_number):
    """Convert 07XXXXXXXX or +2547XXXXXXXX into Daraja's required 2547XXXXXXXX format."""
    phone_number = phone_number.strip().replace(" ", "")
    if phone_number.startswith("+"):
        phone_number = phone_number[1:]
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]
    return phone_number


def initiate_stk_push(phone_number, amount, account_reference="ActivationFee"):
    """
    Trigger an STK Push prompt on the user's phone.
    Returns Daraja's response, which includes CheckoutRequestID to track the transaction.
    """
    access_token = get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        f"{SHORTCODE}{PASSKEY}{timestamp}".encode("utf-8")
    ).decode("utf-8")

    formatted_phone = format_phone_for_mpesa(phone_number)

    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": formatted_phone,
        "PartyB": SHORTCODE,
        "PhoneNumber": formatted_phone,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": "Account activation fee",
    }

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"{DARAJA_BASE_URL}/mpesa/stkpush/v1/processrequest"

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()
