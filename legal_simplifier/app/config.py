import os
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

client = Client(api_key=os.environ.get('GOOGLE_API_KEY'))
