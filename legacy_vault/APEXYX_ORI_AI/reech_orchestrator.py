import os
import subprocess
import sys
from google import genai
from google.genai import types

class ReechOrchestrator:
    def __init__(self):
        key = os.environ.get("GOOGLE_API_KEY")
        if not key or len(key) < 30:
            print("❌ Sovereign Error: No valid Neural Key detected.")
            sys.exit(1)
        self.client = genai.Client(api_key=key)
        print("🔱 Reech Agentic Orchestrator: LINK ESTABLISHED.")

    def run_terminal(self, command):
        """Direct Terminal Access."""
        print(f"🛠️ Executing: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

    def live_orchestration(self, goal):
        """Autonomous tool-calling loop."""
        terminal_tool = types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name="run_terminal",
                description="Execute system commands.",
                parameters={"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}
            )
        ])
        
        print(f"🚀 Goal: {goal}")
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=goal,
            config=types.GenerateContentConfig(tools=[terminal_tool])
        )
        
        # Immediate Tool Execution
        if response.candidates[0].content.parts[0].function_call:
            cmd = response.candidates[0].content.parts[0].function_call.args["command"]
            output = self.run_terminal(cmd)
            print(f"✅ Execution Output: {output}")
        else:
            print(f"📊 Intelligence: {response.text}")

if __name__ == "__main__":
    reech = ReechOrchestrator()
    reech.live_orchestration("List the current directory, then create a file called 'SOVEREIGN_ACTIVE.txt' to prove terminal access.")
