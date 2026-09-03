import google.generativeai as genai

GOOGLE_API_KEY = "AIzaSyAg8bTCpyFb9kbbinQuIAhBBcR9JqZ3LLY"
genai.configure(api_key=GOOGLE_API_KEY)

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello")
    print("SUCCESS: ", response.text)
except Exception as e:
    print("ERROR: ", e)
