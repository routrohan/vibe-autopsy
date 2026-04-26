import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()
try:
    tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    res = tavily.search('"Rohan Rout" WARWICK experience education', search_depth="advanced", max_results=6)
    print(res.get("results", []))
except Exception as e:
    print(e)
