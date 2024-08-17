import tkinter as tk
import threading
import speech_recognition as sr
from openai import OpenAI
from gtts import gTTS
import os
import time
from requests.exceptions import HTTPError

# Initialize the speech recognizer
recognizer = sr.Recognizer()

# Set up OpenAI API (replace with your actual API key)
api_key = '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'
client = OpenAI(api_key=api_key)

# Function to capture and recognize speech input
def recognize_speech():
    with sr.Microphone() as source:
        status_label.config(text="Listening... (speak clearly into the microphone)")
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            status_label.config(text="Recognized Text: " + text)
            return text
        except sr.UnknownValueError:
            status_label.config(text="Sorry, I could not understand the audio.")
            return None
        except sr.RequestError:
            status_label.config(text="Network error. Please check your connection.")
            return None

# Function to generate response using LLM
def generate_response(input_text):
    retries = 3
    delay = 1  # Start with 1 second delay
    for attempt in range(retries):
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",  # Use the model you want
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": input_text}
                ]
            )
            response_text = completion.choices[0].message['content'].strip()
            response_label.config(text="Response: " + response_text)
            return response_text
        except HTTPError as e:
            if e.response.status_code == 429:
                # If rate limited, wait and retry
                status_label.config(text="Rate limit exceeded. Retrying...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                response_label.config(text=f"Error generating response: {e}")
                return None
        except Exception as e:
            response_label.config(text=f"Error generating response: {e}")
            return None
    status_label.config(text="Failed after multiple retries.")
    return None

# Function to convert the generated text to speech using gTTS
def speak_response(response_text):
    if response_text:
        tts = gTTS(text=response_text, lang='en')
        tts.save("response.mp3")
        os.system("mpg321 response.mp3")  # You may need to install mpg321 using sudo apt-get install mpg321

# Function to handle the entire process: speech recognition, LLM response, and speech output
def process_speech():
    input_text = recognize_speech()
    if input_text:
        response_text = generate_response(input_text)
        if response_text:
            speak_response(response_text)

# Function to start speech processing in a separate thread (to keep GUI responsive)
def start_processing():
    threading.Thread(target=process_speech).start()

# Setting up the GUI using Tkinter
root = tk.Tk()
root.title("Speech-to-Speech LLM Bot")

# GUI Components
start_button = tk.Button(root, text="Start Listening", command=start_processing)
start_button.pack(pady=10)

status_label = tk.Label(root, text="Press the button to start speaking.")
status_label.pack(pady=10)

response_label = tk.Label(root, text="Response will appear here.")
response_label.pack(pady=10)

# Run the GUI event loop
root.mainloop()
