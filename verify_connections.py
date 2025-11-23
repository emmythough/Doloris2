import os
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()

def verify_connections():
    print("Verifying connections...")
    
    # 1. Verify Supabase
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        supabase = create_client(url, key)
        
        # Try to select from users table (should be empty or have data, but not error)
        response = supabase.table("users").select("*").limit(1).execute()
        print(f"✅ Supabase Connection OK. Users found: {len(response.data)}")
    except Exception as e:
        print(f"❌ Supabase Connection FAILED: {e}")

    # 2. Verify OpenAI
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say 'Hello, World!'"}]
        )
        print(f"✅ OpenAI Connection OK. Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ OpenAI Connection FAILED: {e}")

if __name__ == "__main__":
    verify_connections()
