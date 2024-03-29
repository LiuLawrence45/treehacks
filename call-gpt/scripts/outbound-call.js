require("dotenv").config();

let canMakeCall = true

async function makeOutBoundCall() {
  const accountSid = process.env.TWILIO_ACCOUNT_SID;
  const authToken = process.env.TWILIO_AUTH_TOKEN;
  
  const client = require('twilio')(accountSid, authToken);

  await client.calls
    .create({
        url: `https://${process.env.SERVER}/incoming`,
        to: process.env.TO_NUMBER,
        from: process.env.FROM_NUMBER
      })
    .then(call => console.log(call.sid));
}

makeOutBoundCall();