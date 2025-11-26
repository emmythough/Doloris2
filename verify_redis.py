import redis
import os
from dotenv import load_dotenv

load_dotenv()

def verify_redis():
    redis_url = os.getenv("REDIS_URL")
    print(f"Testing connection to: {redis_url.split('@')[-1]}") # Hide password
    
    try:
        r = redis.from_url(redis_url)
        r.ping()
        print("[OK] Redis connection successful!")
        
        # Test write/read
        r.set("doloris_test", "ok")
        val = r.get("doloris_test")
        print(f"[OK] Write/Read test: {val.decode('utf-8')}")
        
    except Exception as e:
        print(f"[FAIL] Redis connection failed: {e}")

if __name__ == "__main__":
    verify_redis()
