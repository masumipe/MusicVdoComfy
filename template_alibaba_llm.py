"""
Template for Alibaba Cloud Model Studio Chat Completion

This template demonstrates how to use Alibaba Cloud Model Studio 
with Qwen models (text-only and vision-capable).

Prerequisites:
- Get API Key from: https://www.alibabacloud.com/help/en/model-studio/get-api-key
- Set environment variable: export DASHSCOPE_API_KEY="your_api_key"
  Or on Windows: set DASHSCOPE_API_KEY=your_api_key

Usage:
    python template_alibaba_llm.py
"""

import os
from openai import OpenAI


def create_alibaba_client(workspace_id=None):
    """
    Create and configure the OpenAI client for Alibaba Cloud Model Studio
    
    Args:
        workspace_id: Your Workspace ID (optional, can be in base_url)
    
    Returns:
        OpenAI: Configured client instance
    """
    # Get API key from environment variable or provide directly
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not api_key:
        # Replace with your actual API key if not using environment variable
        api_key = "sk-xxx"  # Replace with your key
    
    # Base URL varies by region
    # Format: https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1
    # Common regions: ap-southeast-1, cn-beijing, cn-shanghai, etc.
    
    if workspace_id:
        base_url = f"https://{workspace_id}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
    else:
        # Use default endpoint without workspace ID
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    
    return client


def chat_completion(client, model, messages):
    """
    Send a chat completion request to Alibaba Cloud
    
    Args:
        client: OpenAI client instance
        model: Model name (e.g., 'qwen-plus', 'qwen-vl-plus', 'qwen-max')
        messages: List of message dictionaries
    
    Returns:
        str: Response content from the model
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error during chat completion: {e}")
        return None


def main():
    # Initialize client
    print("=" * 60)
    print("Alibaba Cloud Model Studio Chat Completion Template")
    print("=" * 60)
    
    # Option 1: Without Workspace ID (using default endpoint)
    client = create_alibaba_client()
    
    # Option 2: With Workspace ID (uncomment and replace with your ID)
    # client = create_alibaba_client(workspace_id="your-workspace-id")
    
    print(f"\nBase URL: {client.base_url}")
    print(f"API Key configured: {'Yes' if client.api_key else 'No'}\n")
    
    if not client.api_key or client.api_key == "sk-xxx":
        print("⚠️  WARNING: Please set your DASHSCOPE_API_KEY environment variable")
        print("   or replace 'sk-xxx' with your actual API key in the code.\n")
        print("   Get API Key: https://www.alibabacloud.com/help/en/model-studio/get-api-key\n")
        return
    
    # Example 1: Text-only chat with qwen-plus
    print("-" * 60)
    print("Example 1: Text Chat (qwen-plus)")
    print("-" * 60)
    
    text_model = "qwen-plus"  # Or: qwen-max, qwen-turbo, etc.
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who are you?"},
    ]
    
    response = chat_completion(client, text_model, messages)
    if response:
        print(f"\nAssistant: {response}\n")
    
    # Example 2: Vision-capable model with image
    print("-" * 60)
    print("Example 2: Vision Chat (qwen-vl-plus)")
    print("-" * 60)
    
    vision_model = "qwen-vl-plus"  # Or: qwen-vl-max, qwen2-vl-7b-instruct, etc.
    
    vision_messages = [{
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"
                }
            },
            {
                "type": "text",
                "text": "What is this?"
            }
        ]
    }]
    
    response = chat_completion(client, vision_model, vision_messages)
    if response:
        print(f"\nAssistant: {response}\n")
    
    # Example 3: Advanced options with thinking control
    print("-" * 60)
    print("Example 3: Advanced Options")
    print("-" * 60)
    
    try:
        completion = client.chat.completions.create(
            model=text_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Explain quantum computing in simple terms."},
            ],
            max_tokens=500,
            temperature=0.7,
            # extra_body={"enable_thinking": False},  # Enable/disable thinking mode
        )
        
        response = completion.choices[0].message.content
        print(f"\nAssistant: {response[:500]}{'...' if len(response) > 500 else ''}\n")
        
        # Print usage information
        if hasattr(completion, 'usage'):
            print(f"Tokens used - Prompt: {completion.usage.prompt_tokens}, "
                  f"Completion: {completion.usage.completion_tokens}\n")
    
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Example 4: Multi-turn conversation
    print("-" * 60)
    print("Example 4: Multi-turn Conversation")
    print("-" * 60)
    
    conversation = [
        {"role": "system", "content": "You are a creative writing assistant."},
        {"role": "user", "content": "Give me a story idea about AI."},
    ]
    
    response = chat_completion(client, text_model, conversation)
    if response:
        print(f"\nAssistant: {response}\n")
        conversation.append({"role": "assistant", "content": response})
        conversation.append({"role": "user", "content": "Make it more dramatic!"})
        
        response = chat_completion(client, text_model, conversation)
        if response:
            print(f"\nAssistant: {response}\n")
    
    print("=" * 60)
    print("Template execution completed!")
    print("=" * 60)
    print("\nModel List: https://www.alibabacloud.com/help/en/model-studio/models")
    print("Documentation: https://www.alibabacloud.com/help/en/model-studio")


if __name__ == "__main__":
    main()
