# Chat Interface Automation

This project implements a flexible chat interface automation system that combines both browser automation and API interactions for maximum reliability and efficiency.

## Features

- Hybrid approach combining Selenium-based browser automation and direct API calls
- Automatic fallback from API to browser automation if API calls fail
- Secure credential management using environment variables
- Headless browser support for background operation

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.template` to `.env` and fill in your credentials:
```bash
cp .env.template .env
```

3. Update the chat interface URL and selectors in `chat_interface.py` to match your target chat interface.

## Usage

```python
from chat_interface import ChatInterface

# Initialize the chat interface
chat = ChatInterface(chat_url="https://your-chat-interface.com")

# Authenticate
chat.get_auth_cookies(username="your_username", password="your_password")

# Send a query and get response
response = chat.send_query("hi", use_api=True)  # Will fall back to browser automation if API fails
print(response)
```

## Configuration

- Update the CSS selectors in `_send_browser_query()` to match your chat interface
- Modify the API endpoint and payload structure in `_send_api_query()` as needed
- Adjust timeouts and wait conditions based on your needs
