# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

# Set environment variables for your credentials
# Read more at http://twil.io/secure

account_sid = "ACbfa59779196ab26978c8dbcf5a0f35f1"
auth_token = "86eb11bd237686ec543ba2782bd961c6"
client = Client(account_sid, auth_token)

call = client.calls.create(
  url="http://demo.twilio.com/docs/voice.xml",
  to="+14406239481",
  from_="+18334842732"
)

print(call.sid)