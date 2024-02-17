require("dotenv").config();

async function makeOutBoundCall() {
  // const accountSid = process.env.TWILIO_ACCOUNT_SID;
  // const authToken = process.env.TWILIO_AUTH_TOKEN;
  const accountSid = "AC1322e254b1ecc1169dc491b8a1984c4a"
  const authToken = "ee5b9136790008927ce2b9d90e566459"
  
  const client = require('twilio')(accountSid, authToken);

  // const axios = require('axios');
  // const response = await axios.get('https://treehacks.ngrok.app/incoming');
  // const twiml = response.data;
  await client.calls
    .create({
        url: `https://treehacks.ngrok.app/incoming`,
        // url: "https://treehacks.ngrok.app/test",
        // twiml: twiml,
        // to: process.env.YOUR_NUMBER,
        // from: process.env.FROM_NUMBER
        to: '+14122251447',
        from: '+18447492281',
      })
    .then(call => console.log(call.sid));
}

makeOutBoundCall();