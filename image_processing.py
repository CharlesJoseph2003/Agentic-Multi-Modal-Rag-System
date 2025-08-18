import os
import base64
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API")
client = OpenAI(api_key = OPENAI_API_KEY)


class ImageProcessing:
    def _init__(self, model="gpt-4.1"):
        self.model = model

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def image_description(self, image_path):
        base64_image = self.encode_image(image_path)
        response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    { "type": "input_text", "text": "The image is coming from construction sites, what is the image in the context of construction?"},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            }
        ],
    )

        return response.output_text
