# store/mpesa.py
import base64
import requests
from datetime import datetime
from django.conf import settings
from requests.auth import HTTPBasicAuth

class MpesaClient:
    def __init__(self):
        self.shortcode = "174379"  # BusinessShortCode
        self.passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.base_url = "https://sandbox.safaricom.co.ke"

    def get_access_token(self):
        """Request access token from Safaricom Daraja"""
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(url, auth=(self.consumer_key, self.consumer_secret))
        response.raise_for_status()
        return response.json()["access_token"]

    def generate_password(self):
        """Generate base64 encoded password"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        data_to_encode = self.shortcode + self.passkey + timestamp
        encoded = base64.b64encode(data_to_encode.encode()).decode("utf-8")
        return encoded, timestamp

    def stk_push(self, phone_number="254708374149", amount=1, account_reference="Test123", transaction_desc="Payment Test"):
        """Initiate STK Push"""
        access_token = self.get_access_token()
        password, timestamp = self.generate_password()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": self.shortcode,   # MUST be your shortcode
            "PhoneNumber": phone_number,
            "CallBackURL": " https://healthful-rosaria-resistible.ngrok-free.dev.app/mpesa/callback/",
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }

        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


# -------------------------
# Helper for Orders
# -------------------------

def initiate_stk_push(order, phone_number="254708374149"):
    """
    Initiates an STK Push request to Safaricom's M-Pesa API (Sandbox).
    """

    # ✅ Correct timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # ✅ Correct password encoding: Shortcode + Passkey + Timestamp
    password_str = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(password_str.encode()).decode("utf-8")

    # ✅ Prepare payload
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(order.total_amount),   # ensure integer
        "PartyA": phone_number,              # MSISDN sending money
        "PartyB": settings.MPESA_SHORTCODE,  # Paybill/till
        "PhoneNumber": phone_number,
        "CallBackURL": f"{settings.BASE_URL}/mpesa/callback/",
        "AccountReference": f"Order{order.id}",
        "TransactionDesc": "Payment for Order",
    }

    # ✅ Headers
    headers = {
        "Authorization": f"Bearer {settings.MPESA_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # ✅ Endpoint
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    # ✅ Send request
    response = requests.post(api_url, json=payload, headers=headers)

    # Debug: print error details
    print("STK Push Response:", response.text)

    # Raise if failed
    response.raise_for_status()
    return response.json()