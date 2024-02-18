# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client

# Set environment variables for your credentials
# Read more at http://twil.io/secure

account_sid = "AC1322e254b1ecc1169dc491b8a1984c4a"
auth_token = "ee5b9136790008927ce2b9d90e566459"
client = Client(account_sid, auth_token)

call = client.calls.create(
  url="http://demo.twilio.com/docs/voice.xml",
  to="+14122251447",
  from_="+18447492281"
)

print(call.sid)