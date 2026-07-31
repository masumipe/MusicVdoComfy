# Alibaba Cloud Model Studio Integration

This project now supports **Alibaba Cloud Model Studio** with the **Qwen3.5-397B-A17B** model.

## Configuration

### 1. Set Your API Key (Required)

Set the `ALIBABA_API_KEY` environment variable **before** running the application:

#### Linux/macOS:
```bash
export ALIBABA_API_KEY="your_api_key_here"
python music_vdo_app.py
```

#### Windows PowerShell:
```powershell
$env:ALIBABA_API_KEY="your_api_key_here"
python music_vdo_app.py
```

#### Windows CMD:
```cmd
set ALIBABA_API_KEY=your_api_key_here
python music_vdo_app.py
```

### 2. Update configure.json

The configuration has been updated to use Alibaba Cloud by default:

```json
{
  "llm": {
    "provider": "alibaba",
    "api_key": "",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "theme_model": "qwen3.5-397b-a17b-2506",
    "vision_model": "qwen3.5-397b-a17b-2506",
    "max_tokens": 800,
    "temperature": 0.7,
    "timeout": 120
  }
}
```

**Note:** Leave `"api_key": ""` in the config file - the key will be loaded from the environment variable automatically.

## How It Works

The LLM client now includes automatic API key resolution:

1. If an API key is provided directly in `configure.json`, it will be used
2. If the API key is empty and provider is `"alibaba"`, it checks for `ALIBABA_API_KEY` environment variable
3. The API key is loaded securely at runtime without storing it in configuration files

## Testing

Run the example script to test your connection:

```bash
export ALIBABA_API_KEY="your_api_key_here"
python example_alibaba_llm.py
```

## Switching Back to Ollama

To switch back to local Ollama:

1. Change `provider` to `"ollama"` in `configure.json`
2. Update `base_url` to `"http://localhost:11434"`
3. Update models to your local Ollama models (e.g., `"qwen3.5:9b"`)

## Security Best Practices

✅ **DO:** Use environment variables for API keys
✅ **DO:** Keep API keys out of version control
❌ **DON'T:** Commit API keys to Git
❌ **DON'T:** Store API keys in plain text config files

## Getting an API Key

1. Visit [Alibaba Cloud Model Studio](https://modelstudio.console.aliyun.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Copy and save it securely

## Supported Features

- ✅ Chat completion (prompt enhancement)
- ✅ Vision/image description
- ✅ Workflow suggestions
- ✅ Pose instructions
- ✅ Video generation instructions

All existing LLM features work seamlessly with Alibaba Cloud!
