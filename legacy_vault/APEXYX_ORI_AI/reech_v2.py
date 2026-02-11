import os
from google import genai
from google.genai.types import Tool, GoogleSearchRetrieval

class ReechSovereign:
    def __init__(self):
        # Initializing Gemini 2.5 Flash for high-leverage reasoning
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        print("🔱 Reech Sovereign Core 2.5 Online.")

    def autonomous_search(self, query):
        """Deep Research & Web-Search Integration."""
        print(f"🔍 Initiating Deep Research: {query}")
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config={'tools': [Tool(google_search_retrieval=GoogleSearchRetrieval())]}
        )
        print(f"📊 Insights: {response.text}")
        return response.text

if __name__ == "__main__":
    reech = ReechSovereign()
    reech.autonomous_search("Identify the top 3 high-ROI ad-revenue strategies for AI-agent apps in 2026")
