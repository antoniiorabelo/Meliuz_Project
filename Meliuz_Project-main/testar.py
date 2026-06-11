import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
CHAVE_API = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=CHAVE_API)

print("Buscando modelos disponíveis para a sua chave...\n")
for modelo in client.models.list():
    # Filtra apenas os modelos que suportam geração de conteúdo
    if "generateContent" in modelo.supported_actions:
        print(f"Nome exato para usar no código: {modelo.name}")