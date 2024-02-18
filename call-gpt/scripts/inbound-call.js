require("dotenv").config();

// You can use this function to make a
// test call to your application by running
// npm inbound
async function makeInboundCall() {
  const VoiceResponse = require('twilio').twiml.VoiceResponse;
  // const accountSid = process.env.TWILIO_ACCOUNT_SID;
  const accountSid = "AC1322e254b1ecc1169dc491b8a1984c4a"
  //const authToken = process.env.TWILIO_AUTH_TOKEN;
  const authToken = "ee5b9136790008927ce2b9d90e566459"
  
  const client = require('twilio')(accountSid, authToken);
  
  // let twiml = new VoiceResponse();
  // // twiml.pause({ length: 10 });
  // twiml.say({voice: 'alice'}, 'oh my god, your friend aaron chang was just violently touched')
  // twiml.pause({ length: 6 });
  // twiml.say({voice: 'alice'}, 'i will call the police for u')
  // twiml.pause({ length: 2 });
  // twiml.say({voice: 'alice'}, 'calling the police right now')
  // // twiml.hangup();

  // console.log(twiml.toString())
  
  await client.calls
    .create({
        url: "https://treehacks.ngrok.app/test",
        // to: process.env.APP_NUMBER,
        // from: process.env.FROM_NUMBER
        to: '+14122251447',
        from: '+18447492281'
      })
    .then(call => console.log(call.sid));
}  

makeInboundCall();