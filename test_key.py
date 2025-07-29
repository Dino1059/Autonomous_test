import os
print("Before loading .env:")
print("OPENAI_API_KEY =", os.environ.get("OPENAI_API_KEY"))

from dotenv import load_dotenv
load_dotenv()

print("After loading .env:")
print("OPENAI_API_KEY =", os.environ.get("OPENAI_API_KEY"))