import os
from groq import Groq
client = Groq(api_key=os.environ.get("GROQ_KEY", ""))
models = client.models.list()
for m in models.data:
    if "vision" in m.id.lower() or "llava" in m.id.lower() or "11b" in m.id.lower() or "90b" in m.id.lower() or "llama-3.2" in m.id.lower():
        print(m.id)
