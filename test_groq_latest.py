#!/usr/bin/env python3
"""
Test script for the latest Groq 1.0.0 client
"""
import asyncio
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from groq import AsyncGroq

async def test_groq_direct():
    """Test Groq API directly with AsyncGroq client"""
    try:
        print("Testing Groq API with AsyncGroq client...")

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("❌ GROQ_API_KEY not set in environment")
            return False
        
        # Initialize client
        client = AsyncGroq(api_key=api_key)
        print("✓ AsyncGroq client initialized successfully")
        
        # Test connection with a simple request
        response = await client.chat.completions.create(
            messages=[
                {"role": "user", "content": "Say 'Hello from Groq!'"}
            ],
            model="llama-3.1-8b-instant",
            max_tokens=10
        )
        
        print("✓ Connection successful!")
        print(f"Response: {response.choices[0].message.content}")
        print(f"Model used: {response.model}")
        if response.usage:
            print(f"Tokens used: {response.usage.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_groq_service():
    """Test the updated GroqService"""
    try:
        print("\nTesting GroqService...")
        
        # Import after setting up path
        from backend.services.groq_service import GroqService
        
        service = GroqService()
        print("✓ GroqService initialized")
        
        # Test connection
        is_connected = await service.check_connection()
        if is_connected:
            print("✓ GroqService connection test passed")
            
            # Test response generation
            response = await service.generate_response("Say hello!")
            print(f"✓ Response generated: {response[:50]}...")
            return True
        else:
            print("❌ GroqService connection test failed")
            return False
            
    except Exception as e:
        print(f"❌ GroqService error: {e}")
        return False

async def main():
    """Main test function"""
    print("=" * 50)
    print("Testing Groq 1.0.0 Integration")
    print("=" * 50)
    
    # Test direct client
    direct_test = await test_groq_direct()
    
    # Test service
    service_test = await test_groq_service()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Direct AsyncGroq client: {'✓ PASS' if direct_test else '❌ FAIL'}")
    print(f"GroqService wrapper: {'✓ PASS' if service_test else '❌ FAIL'}")
    print("=" * 50)
    
    return direct_test and service_test

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)