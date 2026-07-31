"""
Example usage of Alibaba Cloud Model Studio with Qwen3.5-397B-A17B

Before running this script, set your API key in the environment:
    export ALIBABA_API_KEY="your_api_key_here"

Or on Windows PowerShell:
    $env:ALIBABA_API_KEY="your_api_key_here"

Or on Windows CMD:
    set ALIBABA_API_KEY=your_api_key_here
"""

import os
from core.llm_client import LLMClient

# Method 1: Using environment variable (RECOMMENDED)
# Make sure to set ALIBABA_API_KEY environment variable before running
llm_client = LLMClient(
    provider="alibaba",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="",  # Leave empty to use ALIBABA_API_KEY env var
    model="qwen3.5-397b-a17b-2506",
    vision_model="qwen3.5-397b-a17b-2506",
    max_tokens=800,
    temperature=0.7,
    timeout=120
)

# Method 2: Direct API key (less secure)
# llm_client = LLMClient(
#     provider="alibaba",
#     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
#     api_key="sk-xxxxxxxxxxxxxxxx",  # Your API key here
#     model="qwen3.5-397b-a17b-2506",
# )

if __name__ == "__main__":
    # Test the connection
    print("Testing Alibaba Cloud Model Studio connection...")
    print(f"Provider: {llm_client.provider}")
    print(f"Base URL: {llm_client.base_url}")
    print(f"Model: {llm_client.model}")
    print(f"API Key configured: {'Yes' if llm_client.api_key else 'No'}")
    
    if not llm_client.api_key:
        print("\n⚠️  WARNING: No API key found!")
        print("Please set the ALIBABA_API_KEY environment variable:")
        print("  - Linux/Mac: export ALIBABA_API_KEY='your_key'")
        print("  - Windows PowerShell: $env:ALIBABA_API_KEY='your_key'")
        print("  - Windows CMD: set ALIBABA_API_KEY=your_key")
    else:
        print("\n✓ API key loaded successfully!")
        
        # Test chat completion
        print("\n--- Testing Chat Completion ---")
        response = llm_client.chat(
            messages=[{"role": "user", "content": "Hello! Please introduce yourself."}],
            system_prompt="You are a helpful AI assistant powered by Qwen3.5."
        )
        
        if response:
            print(f"\nResponse received ({len(response)} chars):")
            print(response[:500] + "..." if len(response) > 500 else response)
        else:
            print("❌ Failed to get response from API")
        
        # Test prompt enhancement
        print("\n--- Testing Prompt Enhancement ---")
        enhanced = llm_client.enhance_prompt(
            theme="A cyberpunk city at night with neon lights"
        )
        
        if enhanced:
            print(f"\nEnhanced prompt preview:")
            print(enhanced.get('enhanced_prompt', '')[:300] + "...")
        else:
            print("❌ Failed to enhance prompt")
