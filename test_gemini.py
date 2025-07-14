#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/rvan/repos/valken_labs/smairt-recipe/backend')

def test_gemini_simple():
    """Test if Gemini API is working with a simple text query"""
    try:
        print("🔍 Testing Gemini text generation...")
        
        import google.generativeai as genai
        from config import Config
        
        if not Config.GEMINI_API_KEY:
            print("❌ No GEMINI_API_KEY found")
            return False
            
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        response = model.generate_content("List 3 common vegetables:")
        print(f"✅ Gemini response: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False

def test_gemini_structured():
    """Test Gemini structured output"""
    try:
        print("🔍 Testing Gemini structured output...")
        
        import google.generativeai as genai
        from config import Config
        import json
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        schema = {
            "type": "object",
            "properties": {
                "vegetables": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["vegetables"]
        }
        
        model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config=genai.GenerationConfig(
            )
        )
        
        response = model.generate_content("List 5 common vegetables")
        result = json.loads(response.text)
        print(f"✅ Structured response: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Structured output test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Gemini API...")
    
    text_works = test_gemini_simple()
    if text_works:
        structured_works = test_gemini_structured()
        
        if structured_works:
            print("✅ Gemini API is working correctly!")
            print("💡 The issue is likely in the server integration, not the API")
        else:
            print("⚠️ Gemini text works but structured output has issues")
    else:
        print("❌ Gemini API is not working - check your API key and quota")