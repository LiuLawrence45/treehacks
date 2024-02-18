# Horus

## Inspiration
As a team, we're all close with our grandparents. As they get older, we want to be able to support them in any way that we can, even when we can't be there. Our ideation focus started out on elderly care homes--we wanted to devise a system to help keep an eye out for elderly patients, especially those who could be prone to falling or wandering off due to a condition like Alzheimer's.

But we realized that interactive and accessible security isn't just limited to elderly care homes. From consumer usage with parents, to enterprise-level usage at companies that need real-time security monitoring, interactive security is largely lacking. 

## What it does
Our pipeline takes in live stream of videos, and leveraging zero-shot action recognition, we're able to provide real time feedback on chunks of videos that are of interest. Users are able to input with natural language, what they would consider "flaggable" behavior. We match chunks with flaggable behavior, and then, if an incident is flagged, real-time deployment of Twilio API calls the user who deployed the software. The user is then notified of the incident, and able to talk to Twilio about 
      1. Context of the incident
      2. Possible next steps to take
      3. Extractive video

all sent to their phone in real time w/ real phone-call interaction. 


## How we built it

1. Computer Vision.

Azure + YoloV8 integration, to provide holistic view on people actions during frame, with natural language. Multi-threading allows us to achieve this in real-time without much latency. Chunking video based on sections of "similar" actions, to be saved in our DB.  etc etc

Retrieval when necessary, and then all sent to Twilio. 

2. Twilio

Tunneled local server on ngrok so Twilio can access. Then, server receives live requests that uses TwixML to give appropriate responses to users, after running through our fine-tuned GPT. Utilizing whisper, users are able to have real-time conversation with Twilio, who is able to use custom functions and utilities. etc etc 
