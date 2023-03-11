import audioop
import base64
import json
import os
from flask import Flask, request
from flask_sock import Sock, ConnectionClosed
from twilio.twiml.voice_response import VoiceResponse, Start
from twilio.rest import Client
import vosk
from pyngrok import ngrok

app = Flask(__name__)
sock = Sock(app)

TWILIO_ACCOUNT_SID='AC1d3e6366a51ce7f3825b374bbb3bb173';
TWILIO_AUTH_TOKEN='2dd03db32a703f80aa7aa79b5390250c';
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
model = vosk.Model('model')

CL = '\x1b[0K'
BS = '\x08'


@app.route('/', methods=['GET'])
def getSimpleReq():
    """Accept simple request"""
    return str('<h1>you are on our web</h1>'), 200, {'Content-Type': 'text/xml'}

@app.route('/userinfo', methods=['POST'])
def getUserInfo():
    """Accept userinfo"""
    
    data = request.data
    print(data)
    return str('good'), 200, {'Content-Type': 'text/html'}

@app.route('/call', methods=['POST'])
def call():
    """Accept a phone call."""
    response = VoiceResponse()
    start = Start()
    start.stream(url=f'wss://{request.host}/stream')
    response.append(start)
    response.say(" Emergency number 112 ,kindly answer the questions asked and ensure gps enabled. What is your name?")
    response.pause(length=6)
    response.say("Please tell us nature of emergency like fire, accident, crime")
    response.pause(length=6)
    response.say("Any injuries or medical conditions?")
    response.pause(length=15)
    response.say("Anyone in immediate danger or trapped?")
    response.pause(length=15)
    response.say("Extra info you need to provide?")
    response.pause(length=20)

    response.say("Thank you we are generating your ticket and providing help to you with the help of authorities as soon as possible")

    print(f'Incoming call from {request.form["From"]}')
    return str(response), 200, {'Content-Type': 'text/xml'}


@sock.route('/stream')
def stream(ws):
    """Receive and transcribe audio stream."""
    rec = vosk.KaldiRecognizer(model, 16000)
    while True:
        message = ws.receive()
        packet = json.loads(message)
        if packet['event'] == 'start':
            print('Streaming is starting')
        elif packet['event'] == 'stop':
            print('\nStreaming has stopped')
        elif packet['event'] == 'media':
            audio = base64.b64decode(packet['media']['payload'])
            audio = audioop.ulaw2lin(audio, 2)
            audio = audioop.ratecv(audio, 2, 1, 8000, 16000, None)[0]
            if rec.AcceptWaveform(audio):
                r = json.loads(rec.Result())
                print(CL + r['text'] + ' ', end='', flush=True)
            else:
                r = json.loads(rec.PartialResult())
                print(CL + r['partial'] + BS * len(r['partial']), end='', flush=True)


if __name__ == '__main__':
    
    port = 5000
    public_url = ngrok.connect(port, bind_tls=True).public_url
    number = twilio_client.incoming_phone_numbers.list()[0]
    number.update(voice_url=public_url + '/call')
    print(f'Waiting for calls on {number.phone_number}')
    print(f'public url is, {public_url}')

    app.run(port=port)