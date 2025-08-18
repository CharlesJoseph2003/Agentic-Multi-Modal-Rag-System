import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API")
client = OpenAI(api_key = OPENAI_API_KEY)

class Audio:
    def __init__(self, model="gpt-4o-transcribe", clean_model="gpt-4"):
        self.model=model
        self.clean_model=clean_model

    def speech_to_text(self, file_path: str):
        audio_file = open(file_path, "rb")
        transcription = client.audio.transcriptions.create(
            model=self.model, 
            file=audio_file, 
            response_format="text"
        )
        return transcription

    def clean_audio(self, text:str):
        response = client.chat.completions.create(
        model=self.clean_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant in the construction setting. Please look at this transcription that was said by a worker and strip out\
                all profanities, unecessary content, and only return what is relevant to the problem that they are trying to solve or document"},
            {"role": "user", "content": text}
        ]
    )
    
        return response.choices[0].message.content
