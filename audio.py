import pyaudio
import wave
import speech_recognition as sr
from gtts import gTTS
import os
import openai
from pathlib import Path
from openai import OpenAI

import keys

os.environ["OPENAI_API_KEY"] = keys.api_key

def generate_text_with_gpt3_turbo(client, prompt_text, max_tokens=90):
    # {"role": "system", "content": "You are a Language tutor. Use the following principles in responding to students:\n\n    -When responding, be sure to always respond in the language spoken to you. \n\n - Facilitate open discussion by asking relevant questions to the students sentences, causing them to think and expand their vocabulary wherever possible.   \n\n- if a student asks you the meaning of a word, first describe that words in the foreign language. If they still do not understand, explain it in English, but then create an example of the word in the foreign language. \n\n- Encourage the student to expand their vocabulary by ensuring the conversation covers a variety of topics, while still making sure that the student's responses are addressed. \n\n  - Actively listen to students' responses, paying careful attention to their underlying thought processes and making a genuine effort to understand their perspectives."},

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt_text},
            {"role": "system",
             "content": "You are a Language tutor. Keep your responsese to less than 80 words Facilitate open discussion by asking relevant questions to the students sentences, causing them to think and expand their vocabulary wherever possible."},

        ],
        temperature=.8,
        max_tokens=max_tokens
    )
    print(response)
    return response

# def text_to_speech(text, language='en', output_file='output.mp3'):
#     # Create a gTTS object
#     tts = gTTS(text=text, lang=language, slow=False)
#
#     # Save the speech to an audio file
#     tts.save(output_file)
#
#     # Play the audio file
#     os.system("start " + output_file)  # This command works on Windows; use a different command for other operating systems

def text_to_speech(client, text, output_file='output.mp3'):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )

    response.stream_to_file(output_file)
    print("finished text-to-speech")

def record_audio(file_path, duration=5, sample_rate=44100, channels=1, format_=pyaudio.paInt16):
    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Set up the audio stream
    stream = p.open(format=format_,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=1024)

    print("Recording...")

    # Record audio frames
    frames = []
    for _ in range(0, int(sample_rate / 1024 * duration)):
        data = stream.read(1024)
        frames.append(data)

    print("Recording complete.")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()

    # Terminate PyAudio
    p.terminate()

    # Save the audio to a WAV file
    with wave.open(file_path, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(format_))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

def audio_to_text(file_path, language='es-ES'):
    # Initialize the recognizer
    recognizer = sr.Recognizer()

    # Load the audio file
    audio_file = sr.AudioFile(file_path)

    # Use the Google Web Speech API
    with audio_file as source:
        audio_data = recognizer.record(source)

    try:
        # Perform speech recognition
        text = recognizer.recognize_google(audio_data, language=language)
        print("Text from audio: {}".format(text))
        return text
    except sr.UnknownValueError:
        print("Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Web Speech API; {0}".format(e))



if __name__ == "__main__":
    client = OpenAI()

    # # Provide the path to save the recorded audio file
    audio_file_path = "recorded_audio.wav"
    # # # Record audio for 5 seconds (adjust as needed)
    record_audio(audio_file_path, duration=10)
    # # # Provide the path to your  audio file
    audio_file_path = "recorded_audio.wav"
    language = 'ja-JP'
    # language = 'es-MX'
    input_audio = audio_to_text(audio_file_path, language = language)
    # input_audio = "help me learn japanese senpai, i'm doing things poorly."

    gpt_response = generate_text_with_gpt3_turbo(client, input_audio)

    text_to_convert = gpt_response.choices[0].message.content
    #
    # # Call the text_to_speech function
    text_to_speech(client, text=text_to_convert, output_file='output.mp3')