import os

def verify_assets():
    print("🔱 APEX AGENT: RUNNING ASSET INTEGRITY AUDIT...")
    # Checking for the tool map we injected in V51.0
    if os.path.exists('agent_tool_map.txt'):
        with open('agent_tool_map.txt', 'r') as f:
            tools = f.readlines()
            print(f"📡 Found {len(tools)} tools ready for execution.")
    else:
        print("⚠️ Warning: agent_tool_map.txt not found in local root.")

if __name__ == "__main__":
    verify_assets()
