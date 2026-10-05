import os
from intasend import APIService

INTASEND_PUBLISHABLE_KEY = os.getenv("INTASEND_PUBLISHABLE_KEY")
INTASEND_SECRET_KEY = os.getenv("INTASEND_SECRET_KEY")
INTASEND_TEST_MODE = os.getenv("INTASEND_TEST_MODE", "true").lower() == "true"

service = APIService(
    token=INTASEND_SECRET_KEY,
    publishable_key=INTASEND_PUBLISHABLE_KEY,
    test=INTASEND_TEST_MODE,
)


def format_phone_for_intasend(phone_number):
    phone_number = phone_number.strip().replace(" ", "")
    if phone_number.startswith("+"):
        phone_number = phone_number[1:]
    if phone_number.startswith("0"):
        phone_number = "254" + phone_number[1:]
    return phone_number


def initiate_stk_push(phone_number, amount, email, narrative="ActivationFee"):
    formatted_phone = format_phone_for_intasend(phone_number)
    response = service.collect.mpesa_stk_push(
        phone_number=formatted_phone,
        email=email,
        amount=float(amount),
        narrative=narrative,
    )
    return response