import os
from fastapi import FastAPI
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI(title="LLM Gateway")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/")
def health_check():
    return {"status": "LLM Gateway running"}

@app.post("/generate")
def generate(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=50
    )

    return {
        "response": response.choices[0].message.content,
        "usage": response.usage.total_tokens
    }
