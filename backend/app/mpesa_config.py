import requests
import base64
from datetime import datetime
from config import Config

class MpesaAPI:
    def __init__(self):
        self.base_url = Config.MPESA_BASE_URL
        self.consumer_key = Config.MPESA_CONSUMER_KEY
        self.consumer_secret = Config.MPESA_CONSUMER_SECRET
        self.business_number = Config.MPESA_BUSINESS_NUMBER
        self.account_number = Config.MPESA_ACCOUNT_NUMBER
        self.access_token = None

    def get_access_token(self):
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        auth = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            return self.access_token
        else:
            raise Exception("Failed to get access token")

    def initiate_payment(self, phone_number, amount, callback_url, account_reference, transaction_desc):
        if not self.access_token:
            self.get_access_token()

        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f"{self.business_number}{Config.MPESA_PASSKEY}{timestamp}".encode()).decode()
        
        data = {
            "BusinessShortCode": self.business_number,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": self.business_number,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": self.account_number,
            "TransactionDesc": transaction_desc
        }

        response = requests.post(url, json=data, headers=headers)
        return response.json()

mpesa_api = MpesaAPI()