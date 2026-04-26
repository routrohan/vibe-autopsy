import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()
try:
    print("Tavily API Key:", os.getenv("TAVILY_API_KEY"))
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    res = tavily.search("Rohan Rout")
    print(res.get("results", []))
except Exception as e:
    print(e)
