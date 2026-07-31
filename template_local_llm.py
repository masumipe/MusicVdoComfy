"""
Template for Local LLM Chat Completion (Ollama-compatible)

This template demonstrates how to use local LLM models via Ollama or 
other OpenAI-compatible local servers.

Prerequisites:
- Install Ollama: https://ollama.ai
- Pull a model: ollama pull qwen2.5:7b  (or any other model)
- Start Ollama server: ollama serve

Usage:
    python template_local_llm.py
"""

import os
from openai import OpenAI


def create_local_client():
    """
    Create and configure the OpenAI client for local LLM
    
    Returns:
        OpenAI: Configured client instance
    """
    client = OpenAI(
        # Local LLMs typically don't require an API key
        api_key="ollama",  # Can be any non-empty string for Ollama
        # Default Ollama endpoint
        base_url="http://localhost:11434/v1",
    )
    return client


def chat_completion(client, model, messages):
    """
    Send a chat completion request to local LLM
    
    Args:
        client: OpenAI client instance
        model: Model name (e.g., 'qwen2.5:7b', 'llama3.2', 'mistral')
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
    print("Local LLM Chat Completion Template")
    print("=" * 60)
    
    client = create_local_client()
    
    # Configure your local model here
    # Common models: qwen2.5:7b, llama3.2, mistral, codellama, etc.
    MODEL_NAME = "qwen2.5:7b"
    
    print(f"\nUsing model: {MODEL_NAME}")
    print("Make sure Ollama is running and the model is pulled!\n")
    
    # Example 1: Simple text chat
    print("-" * 60)
    print("Example 1: Simple Text Chat")
    print("-" * 60)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who are you?"},
    ]
    
    response = chat_completion(client, MODEL_NAME, messages)
    if response:
        print(f"\nAssistant: {response}\n")
    
    # Example 2: Multi-turn conversation
    print("-" * 60)
    print("Example 2: Multi-turn Conversation")
    print("-" * 60)
    
    conversation = [
        {"role": "system", "content": "You are a creative writing assistant."},
        {"role": "user", "content": "Give me a story idea about a robot."},
    ]
    
    response = chat_completion(client, MODEL_NAME, conversation)
    if response:
        print(f"\nAssistant: {response}\n")
        # Continue the conversation
        conversation.append({"role": "assistant", "content": response})
        conversation.append({"role": "user", "content": "Make it more exciting!"})
        
        response = chat_completion(client, MODEL_NAME, conversation)
        if response:
            print(f"\nAssistant: {response}\n")
    
    # Example 3: Code generation
    print("-" * 60)
    print("Example 3: Code Generation")
    print("-" * 60)
    
    code_messages = [
        {"role": "system", "content": "You are an expert Python programmer."},
        {"role": "user", "content": "Write a function to calculate fibonacci numbers."},
    ]
    
    response = chat_completion(client, MODEL_NAME, code_messages)
    if response:
        print(f"\nAssistant:\n{response}\n")
    
    print("=" * 60)
    print("Template execution completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
