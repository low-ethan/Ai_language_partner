import pyaudio
import wave
from threading import Thread
from flask import Flask, render_template
import time
import speech_recognition as sr
import os
from flask import request, url_for
from openai import OpenAI


import keys

app = Flask(__name__)

# Global variables
language = 'en-US'
recording = False
audio_file_path = "recorded_audio.wav"
saved = False
os.environ["OPENAI_API_KEY"] = keys.api_key


def record_audio(file_path, duration=5, sample_rate=44100, channels=1, format_=pyaudio.paInt16):
    global recording
    global saved
    saved = False

    os.remove(audio_file_path)

    p = pyaudio.PyAudio()

    stream = p.open(format=format_,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=1024)

    frames = []

    print("Recording...")

    while recording:
        data = stream.read(1024)
        frames.append(data)

    print("Recording complete.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(format_))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

    saved = True

@app.route('/get_recognized_text')
def audio_to_text():
    global saved
    global language
    while not saved:
        time.sleep(1)
        continue

    recognizer = sr.Recognizer()

    audio_file = sr.AudioFile(audio_file_path)

    with audio_file as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data, language=language)
        print("Text from audio: {}".format(text))
        return text
    except sr.UnknownValueError:
        return "Speech Recognition could not understand audio"
    except sr.RequestError as e:
        return "Could not request results from Google Web Speech API; {0}".format(e)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_record')
def start_record():
    global recording
    global language
    recording = True

    # Get the selected language from the request parameters
    language = request.args.get('language', 'en-US')

    # Start recording in a separate thread, passing the selected language
    record_thread = Thread(target=record_audio, args=(audio_file_path, language))
    record_thread.start()

    return 'Recording started!'

@app.route('/stop_record')
def stop_record():
    global recording
    recording = False
    return 'Recording stopped!'

@app.route('/generate_text', methods=['POST'])
def generate_text():
    client = OpenAI()  # Make sure to import and initialize your OpenAI client
    prompt_text = request.json['prompt_text']
    # generated_text = prompt_text
    response = generate_text_with_gpt3_turbo(client, prompt_text)
    generated_text = response.choices[0].message.content
    return generated_text

def generate_text_with_gpt3_turbo(client, prompt_text, max_tokens=150):
    # {"role": "system", "content": "You are a Language tutor. Use the following principles in responding to students:\n\n    -When responding, be sure to always respond in the language spoken to you. \n\n - Facilitate open discussion by asking relevant questions to the students sentences, causing them to think and expand their vocabulary wherever possible.   \n\n- if a student asks you the meaning of a word, first describe that words in the foreign language. If they still do not understand, explain it in English, but then create an example of the word in the foreign language. \n\n- Encourage the student to expand their vocabulary by ensuring the conversation covers a variety of topics, while still making sure that the student's responses are addressed. \n\n  - Actively listen to students' responses, paying careful attention to their underlying thought processes and making a genuine effort to understand their perspectives."},

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt_text},
            {"role": "system",
             "content": "You are a Language tutor. Keep your responsese to less than 40 words Facilitate discussion by asking relevant questions, causing them to think and expand their vocabulary. Respond in the langauge that was spoken to you."},
        ],
        temperature=.8,
        max_tokens=max_tokens
    )
    print(response)
    return response

def text_to_speech_one(client, text, output_file='output.mp3'):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    response.stream_to_file(output_file)
    print("finished text-to-speech")

@app.route('/text_to_speech', methods=['POST'])
def text_to_speech():
    client = OpenAI()  # Make sure to import and initialize your OpenAI client
    text = request.json['text']
    audio_file_path = "static/mp3/output.mp3"  # You can adjust the file path as needed
    try:
        os.remove(audio_file_path)
    except OSError:
        pass
    text_to_speech_one(client, text, output_file=audio_file_path)
    return url_for('static', filename='mp3/output.mp3')
    # return audio_file_path


if __name__ == "__main__":
    app.run(debug=True)
