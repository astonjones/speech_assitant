## This is a speech assistant project

1.) Allow wake words using Picovoice porcupine

2.) After wake word is detected then use Picovoice Cheetah to convert speech to Text

3.) Once speech is converted to text, push text to ChatGPT API

4.) Once text is recieved from CHATPGT API use google text to speech

5.) Profit?!

## Setup

Set environment variable on host machine:

OPENAI_ACCESS_KEY=<insert_access_key>

install necessary imports through pip

Install google client tools

Setup a project in google and run "gcloud auth login" to sign in

Create a service account for google text to speech

run command:

python speech_assistant_mic.py --access_key <insert_pv_access_key> --keywords <wake_word>

say jarvis to access chat prompt

