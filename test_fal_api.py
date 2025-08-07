#!/usr/bin/env python3
"""
Simple test script to check if FAL API is working.
This will help us determine if FAL API calls are causing the MCP tool hangs.
"""

import asyncio
import os
from pathlib import Path

# Load environment from .env file (same as MCP server does)
def load_env_file():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = value.strip()

load_env_file()

FAL_API_KEY = os.environ.get("FAL_KEY")
print(f"FAL_API_KEY loaded: {'Yes' if FAL_API_KEY else 'No'}")
print(f"FAL_API_KEY (first 10 chars): {FAL_API_KEY[:10] if FAL_API_KEY else 'None'}...")

if not FAL_API_KEY:
    print("❌ No FAL API key found - exiting")
    exit(1)

# Test imports
try:
    import requests
    print("✅ requests library available")
except ImportError:
    print("❌ requests library not available")
    exit(1)

async def test_fal_api():
    """Test basic FAL API connectivity and simple image generation"""
    
    print("\n🔍 Testing FAL API connectivity...")
    
    headers = {
        "Authorization": f"Key {FAL_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # Simple test payload - basic image generation
    payload = {
        "prompt": "A simple red circle on white background",
        "image_size": "square_hd",  # 1024x1024
        "num_inference_steps": 20,  # Faster generation
        "guidance_scale": 3.5,
        "num_images": 1
    }
    
    url = "https://fal.run/fal-ai/flux-lora"  # Based on worldbuilding code
    
    try:
        print(f"🚀 Making request to: {url}")
        print(f"📝 Prompt: {payload['prompt']}")
        
        # Add timeout to prevent hanging
        response = requests.post(url, json=payload, headers=headers, timeout=30.0)
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📏 Response size: {len(response.content)} bytes")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ FAL API call successful!")
            print(f"🔗 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            if isinstance(result, dict) and 'images' in result:
                print(f"🖼️  Generated {len(result['images'])} image(s)")
                for i, img in enumerate(result['images']):
                    if isinstance(img, dict) and 'url' in img:
                        print(f"   Image {i+1} URL: {img['url'][:50]}...")
        else:
            print(f"❌ FAL API call failed!")
            print(f"📄 Response text: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("⏰ FAL API call timed out after 30 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print("🌐 Connection error - can't reach FAL API")
        return False
    except Exception as e:
        print(f"💥 Unexpected error: {str(e)}")
        return False
    
    return response.status_code == 200

if __name__ == "__main__":
    print("🧪 FAL API Test Script")
    print("=" * 40)
    
    # Run the async test
    success = asyncio.run(test_fal_api())
    
    print("\n" + "=" * 40)
    if success:
        print("✅ FAL API appears to be working")
        print("   → This is likely NOT the cause of MCP tool hangs")
    else:
        print("❌ FAL API has issues")
        print("   → This could be causing MCP tool hangs!")
        print("   → Consider temporarily disabling FAL API in MCP server")
    print("=" * 40)