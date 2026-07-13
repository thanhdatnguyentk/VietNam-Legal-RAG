from langchain_google_genai import ChatGoogleGenerativeAI
from vietnam_legal_rag.config import get_settings
settings = get_settings()
for model_name in ["gemini-pro", "gemini-1.0-pro", "gemini-1.5-pro", "gemini-1.5-flash"]:
    try:
        llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=settings.gemini_api_key)
        res = llm.invoke("Hi")
        print(f"{model_name}: Success! {res.content}")
        break
    except Exception as e:
        print(f"{model_name}: Failed - {e}")
