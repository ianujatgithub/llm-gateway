import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
    model="gpt-4o-mini",   # small + affordable model
    messages=[
        {"role": "user", "content": "Explain caching in one short sentence."}
    ],
    max_tokens=30
)

print("Response:")
print(response.choices[0].message.content)

print("\nToken Usage:")
print(response.usage)
