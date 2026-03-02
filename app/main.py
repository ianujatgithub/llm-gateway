import os
import time
import logging
import uuid
from fastapi import FastAPI, HTTPException
from fastapi import Request
from collections import defaultdict
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI
from app.services.openai_service import OpenAIService
from openai import OpenAIError

load_dotenv()

app = FastAPI(title="LLM Gateway")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llm_gateway")
# Simple in-memory rate limiter
request_counts = defaultdict(list)
RATE_LIMIT = 5
WINDOW_SECONDS = 60
llm_service = OpenAIService()

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500)

class GenerateResponse(BaseModel):
    response: str
    total_tokens: int

@app.get("/")
def health_check():
    return {"status": "LLM Gateway running"}
@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest, http_request: Request):
    endpoint_start = time.time()
    client_ip = http_request.client.host
    current_time = time.time()
    # Remove expired timestamps
    request_counts[client_ip] = [
    timestamp for timestamp in request_counts[client_ip]
    if current_time - timestamp < WINDOW_SECONDS
    ]

    if len(request_counts[client_ip]) >= RATE_LIMIT:
    	raise HTTPException(status_code=429, detail="Rate limit exceeded")

    request_counts[client_ip].append(current_time)
    request_id = str(uuid.uuid4())
    logger.info(f"Request {request_id} received")
    if len(request.prompt) > 2000:
    	raise HTTPException(status_code=400, detail="Prompt too long")

    max_retries = 3
    backoff = 1

    for attempt in range(max_retries):
        try:
            start_time = time.time()
            result = llm_service.generate(request.prompt)
            duration = time.time() - start_time
            prompt_tokens = result["prompt_tokens"]
            completion_tokens = result["completion_tokens"]
            total_tokens = result["total_tokens"]
            response_text = result["response"]
            input_cost_per_1k = 0.00015
            output_cost_per_1k = 0.0006
            estimated_cost = ((prompt_tokens / 1000) * input_cost_per_1k + (completion_tokens / 1000) * output_cost_per_1k)
            endpoint_duration = time.time() - endpoint_start
            logger.info(
                f"Request {request_id} success | "
                f"prompt_tokens={prompt_tokens} | "
                f"completion_tokens={completion_tokens} | "
                f"total_tokens={total_tokens} | "
                f"cost_estimate=${estimated_cost:.6f} | "
                f"model_latency={duration:.2f}s | "
                f"endpoint_latency={endpoint_duration:.2f}s | "
                f"attempt={attempt+1}"
            )
            return GenerateResponse(
            	response=response_text,
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
