import os
import time
import logging
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI
from openai import OpenAIError

load_dotenv()

app = FastAPI(title="LLM Gateway")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_gateway")
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

    request_id = str(uuid.uuid4())
    logger.info(f"Request {request_id} received")
    if len(request.prompt) > 2000:
    	raise HTTPException(status_code=400, detail="Prompt too long")

    max_retries = 3
    backoff = 1

    for attempt in range(max_retries):
        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": request.prompt}
                ],
                max_tokens=50
            )

            duration = time.time() - start_time
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            input_cost_per_1k = 0.00015
            output_cost_per_1k = 0.0006
            estimated_cost = ((prompt_tokens / 1000) * input_cost_per_1k + (completion_tokens / 1000) * output_cost_per_1k)
            logger.info(
                f"Request {request_id} success | "
                f"prompt_tokens={prompt_tokens} | "
                f"completion_tokens={completion_tokens} | "
                f"total_tokens={total_tokens} | "
                f"cost_estimate=${estimated_cost:.6f} | "
                f"duration={duration:.2f}s | "
                f"attempt={attempt+1}"
            )

            return GenerateResponse(
                response=response.choices[0].message.content,
                total_tokens=total_tokens
            )

        except OpenAIError as e:
            logger.warning(
                f"Request {request_id} failed attempt {attempt+1}: {str(e)}"
            )

            if attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
            else:
                logger.error(f"Request {request_id} exhausted retries")
                raise HTTPException(status_code=500, detail="LLM service unavailable")

        except Exception as e:
            logger.error(f"Request {request_id} unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail="Unexpected server error")
