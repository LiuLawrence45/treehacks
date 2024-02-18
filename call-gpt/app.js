require("dotenv").config();
const express = require("express");
const ExpressWs = require("express-ws");
const colors = require('colors');


const { GptService } = require("./services/gpt-service");
const { StreamService } = require("./services/stream-service");
const { TranscriptionService } = require("./services/transcription-service");
const { TextToSpeechService } = require("./services/tts-service");

const app = express();
ExpressWs(app);

const PORT = process.env.PORT || 3000;

// app.post("/incoming", (req, res) => {
//   res.status(200);
//   res.type("text/xml");
//   res.end(`
//   <Response>
//     <Connect>
//       <Stream url="wss://${process.env.SERVER}/connection" />
//     </Connect>
//   </Response>
//   `);
// });

app.post("/incoming", (req, res) => {
  res.status(200);
  res.type("text/xml");
  res.end(`
  <Response>
    <Connect>
      <Stream url="wss://${process.env.SERVER}/connection" />
    </Connect>
  </Response>
  `);
});



app.ws("/connection", (ws, req) => {
  ws.on("error", console.error);
  console.log((console.error).red)
  // Filled in from start message
  let streamSid;

  const gptService = new GptService();
  const streamService = new StreamService(ws);
  const transcriptionService = new TranscriptionService();
  const ttsService = new TextToSpeechService({});
  
  let marks = []
  let interactionCount = 0

  // Incoming from MediaStream
  ws.on("message", async function message(data) {
    const msg = JSON.parse(data);
    if (msg.event === "start") {
      streamSid = msg.start.streamSid;
      streamService.setStreamSid(streamSid);
      console.log(`Twilio -> Starting Media Stream for ${streamSid}`.underline.red);
      try {
        const response = await fetch('http://127.0.0.1:5000/data'); // Replace with your actual URL
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        const initialMessage = data.assistantPrompt; // Replace fieldName with the actual field you need

        // Use the fetched initialMessage in your ttsService.generate call
        ttsService.generate({ partialResponseIndex: null, partialResponse: initialMessage }, 1);
      } catch (error) {
        console.error('Failed to fetch initial message:', error);
        // Handle error, possibly send an error message back via WebSocket
      }
    } else if (msg.event === "media") {
      transcriptionService.send(msg.media.payload);
    } else if (msg.event === "mark") {
      const label = msg.mark.name;
      console.log(`Twilio -> Audio completed mark (${msg.sequenceNumber}): ${label}`.red)
      marks = marks.filter(m => m !== msg.mark.name)
    } else if (msg.event === "stop") {
      console.log(`Twilio -> Media stream ${streamSid} ended.`.underline.red)
    }
  });

  transcriptionService.on("utterance", async (text) => {
    // This is a bit of a hack to filter out empty utterances
    if(marks.length > 0 && text?.length > 5) {
      console.log("Twilio -> Interruption, Clearing stream".red)
      ws.send(
        JSON.stringify({
          streamSid,
          event: "clear",
        })
      );
    }
  });

  transcriptionService.on("transcription", async (text) => {
    if (!text) { return; }
    console.log(`Interaction ${interactionCount} – STT -> GPT: ${text}`.yellow);
    gptService.completion(text, interactionCount);
    interactionCount += 1;
  });
  
  gptService.on('gptreply', async (gptReply, icount) => {
    console.log(`Interaction ${icount}: GPT -> TTS: ${gptReply.partialResponse}`.green )
    ttsService.generate(gptReply, icount);
  });

  ttsService.on("speech", (responseIndex, audio, label, icount) => {
    console.log(`Interaction ${icount}: TTS -> TWILIO: ${label}`.blue);

    streamService.buffer(responseIndex, audio);
  });

  streamService.on('audiosent', (markLabel) => {
    marks.push(markLabel);
  })
});

app.listen(PORT);
console.log(`Server running on port ${PORT}`);
