import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI(title="LLM Gateway")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500)

class GenerateResponse(BaseModel):
    response: str
    total_tokens: int

@app.get("/")
def health_check():
    return {"status": "LLM Gateway running"}

@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": request.prompt}
            ],
            max_tokens=50
        )

        return GenerateResponse(
            response=response.choices[0].message.content,
            total_tokens=response.usage.total_tokens
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

