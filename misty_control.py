import json, os
import requests
import websocket
import threading
import openai
import base64
import time
import signal
import sys



class Misty():
    def __init__(self, misty_ip):
        # super().__init__()
        self.misty_ip = misty_ip
        self.set_up_misty_api()
        self.set_up_misty_websockets()
        self.speaking_complete = False
        self.listening_complete = False

    def set_up_misty_api(self):
        # self.connect_to_misty_api()
        # http://<robot-ip-address>/api/<Endpoint>
        self.speech_endpoint = f"http://{self.misty_ip}/api/tts/speak" # either api/tts/speak or api/speak
        self.listen_endpoint = f"http://{self.misty_ip}/api/audio/speech/capture"


    def set_up_misty_websockets(self):
        websocket.enableTrace(True)
        self.ws_voicerecord = websocket.WebSocketApp(f"ws://{self.misty_ip}/pubsub",
                                on_message=self.vr_on_message,
                                on_error=self.vr_on_error,
                                on_close=self.vr_on_close
                    )
        self.ws_voicerecord.on_open = self.vr_on_open

        # text2speech complete
        self.ws_tts_complete = websocket.WebSocketApp(f"ws://{self.misty_ip}/pubsub",
                        on_message=self.ttsc_on_message,
                        on_error=self.ttsc_on_error,
                        on_close=self.ttsc_on_close
            )
        self.ws_tts_complete.on_open = self.ttsc_on_open


    def start_websockets(self):
        # Start VoiceRecord WebSocket in its own thread
        vr_thread = threading.Thread(target=self.setup_voicerecord_ws)
        vr_thread.start()

        # Start TextToSpeechComplete WebSocket in its own thread
        tts_thread = threading.Thread(target=self.setup_texttospeechcomplete_ws)
        tts_thread.start()

    def setup_voicerecord_ws(self):
        # Setup and run the VoiceRecord WebSocket
        self.ws_voicerecord.run_forever()

    def setup_texttospeechcomplete_ws(self):
        # Setup and run the TextToSpeechComplete WebSocket
        self.ws_tts_complete.run_forever()


    def vr_on_open(self, websocket_instance):
        subscribeMsg = {
            "Operation": "subscribe",
            "Type": "VoiceRecord", 
            "DebounceMs": "100", 
            "EventName": "Voice Recording", 
            "ReturnProperty": None,
            "EventConditions": [ 
            ]            
        }
        # sending message to subscribe to certain event
        subscribeMsg = json.dumps(subscribeMsg)
        self.ws_voicerecord.send(subscribeMsg)


    def vr_on_message(self, msg_instance, msg_msg):
        # contains file name of voice recording
        """
        output of message
        {
            "eventName":"VoiceRecord",
            "message": {
                "errorCode":0,
                "errorMessage":"Detected end of voice command.",
                "filename":"capture_HeyMisty.wav",
                "success":true
            }
        }
        """
        if "message" in msg_msg:
            self.listening_complete = True
        # print("\n\nmessage")
        # print(f"{msg_instance=}")
        # print(f"{msg_msg=}")
        # print("\n\n")
        return


    def vr_on_error(self, error_instance, error_msg):
        # print("\n\nerror")
        # print(f"{error_instance=}")
        # print(f"{error_msg=}")
        # print("\n\n")
        pass


    def vr_on_close(self, msg1, msg2, msg3):
        if self.ws_voicerecord is not None:
            self.ws_voicerecord.close()
            # print("VoiceRecord WebSocket closed")

        # print("\n\nclosing ws")
        # print(f"{msg1=}")
        # print(f"{msg2=}")
        # print(f"{msg3=}")
        # print("\n\n")


    def ttsc_on_open(self, websocket_instance):
        subscribeMsg = {
            "Operation": "subscribe",
            "Type": "TextToSpeechComplete", 
            "DebounceMs": "100", 
            "EventName": "TextToSpeechCompleteEvent", 
        }
        # sending message to subscribe to certain event
        subscribeMsg = json.dumps(subscribeMsg)
        self.ws_tts_complete.send(subscribeMsg)
        print("ttsc opened")


    def ttsc_on_message(self, msg_instance, msg_msg):
        """
        output of message

        """
        print("\n\nmessage received ttsc!")
        print(f"{msg_instance=}")
        print(f"{msg_msg=}")
        print("\n\n")
        if "utteranceId" in msg_msg:
            self.speaking_complete = True

    def ttsc_on_error(self, error_instance, error_msg):
        # print("\n\nerror")
        # print(f"{error_instance=}")
        # print(f"{error_msg=}")
        # print("\n\n")
        pass


    def ttsc_on_close(self, msg1, msg2, msg3):
        if self.ws_tts_complete is not None:
            self.ws_tts_complete.close()
            # print("TextToSpeechComplete WebSocket closed")

        # print("\n\nclosing ws")
        # print(f"{msg1=}")
        # print(f"{msg2=}")
        # print(f"{msg3=}")
        # print("\n\n")


    def speak(self, text_to_speech):
        payload = {"Text": f"<speak>{text_to_speech}</speak>", "UtteranceId": "First"}
        # can set "Flush": True to remove all enqued texts, default False
        # other customizations w/ speed of speech but unnecessary 
        print(f"Checkpoint 2: {m.speaking_complete=}")
        res = requests.post(self.speech_endpoint, json=payload)
        print(f"Checkpoint 3: {m.speaking_complete=}")
        # returns an array? true if no errors?
        # if not res.status_code != 200:
        #     print("Misty unable to receive request. Status Code: ", res.status_code)


    def listen(self, MaxSpeechLength, SilenceTimeout):
        
        payload = {"RequireKeyPhrase": False, "OverwriteExisting": True, "MaxSpeechLength": MaxSpeechLength, "SilenceTimeout": SilenceTimeout} 

        # RequireKeyPhrase: False --> immediately start recording 
        # if true, records only when recognizes "key phrase"
        # SilenceTimeout: max duration of silence before listening stops. 2000 means 2 seconds

        res = requests.post(self.listen_endpoint, json=payload)
        # returns an array? true if no errors?
        #The audio file is stored in capture_Dialogue.wav


    def play_audio_file(self):
        payload = {"fileName": "Timmy-Testing.wav", "volume": 20}
        res = requests.post(f"http://{self.misty_ip}/api/audio/play", json=payload)

    def get_audio_file(self):
        #res = requests.get(f"http://{self.misty_ip}/api/audio?FileName=capture_Dialogue.wav")
        res = requests.get(f"http://{self.misty_ip}/api/audio?FileName=capture_Dialogue.wav&Base64=true")

        encode_string = res.json()["result"]["base64"]
        decode_string = base64.b64decode(encode_string)

        media_file = open("capture_Dialogue.wav", "wb")
        media_file.write(decode_string)


    def transcribe_gpt(self):
        media_file = open("capture_Dialogue.wav", 'rb')

        client = openai.OpenAI()
        transcription = client.audio.transcriptions.create(model="whisper-1", file=media_file)

        print("transcription text is: ", transcription.text)
        # llm = ChatOpenAI(model_name="gpt-4") # gpt-3.5-turbo or gpt-4
        # response = llm.invoke(transcription.text).content
        # print("robot says this: ", response)
        # m.speak(response)



def signal_handler(sig, frame):
    # closes web sockets before terminating
    m.ws_voicerecord.on_close(None, None, None)
    m.ws_tts_complete.on_close(None, None, None)
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    f = open("my_API_key.json")
    key_information = json.load(f)
    api_key = key_information['keys'][0]['api_key']
    os.environ["OPENAI_API_KEY"] = api_key
    filename = "capture_Dialogue.wav"
    if os.path.exists(filename):
        os.remove(filename)

    print("check point 1")

    m = Misty(misty_ip="192.168.1.118")
    m.start_websockets()
    # m.speak("Testing")
    # m.ws.run_forever()

    print(f"{m.speaking_complete=}")
    m.speak('What is your name?')
    
    while not m.speaking_complete:
        print(f"Loop: {m.speaking_complete=}")
        time.sleep(0.5)


    m.listen(5000, 2000) # starts listening immediately

    
    # wait till audio captured
    while not m.self.listening_complete:
        print(f"Loop: {m.listening_complete=}")
        time.sleep(0.5)


    m.get_audio_file()

    while True:
        time.sleep(1)
        
        if os.path.exists(filename):
            m.transcribe_gpt()
            m.ws_voicerecord.on_close(None, None, None)
            m.ws_tts_complete.on_close(None, None, None)
            exit()
