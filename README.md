SAM-Pro Discord Bot

SAM-Pro is a Discord bot that leverages OpenAI's GPT models and Stability AI's Stable Diffusion XL to provide a conversational AI experience with image generation capabilities. Users can interact with the bot using slash commands or by mentioning it directly in messages.
Features

    Conversational AI: Engage in conversations with the bot powered by OpenAI's GPT models.
    Per-User Contexts: The bot maintains conversation context individually for each user.
    Custom Personalities: Users can set custom response styles or let the bot generate one randomly.
    Image Generation: Generate images based on prompts using Stable Diffusion Ultra.
    Slash Commands: Easy-to-use slash commands for all functionalities.
    Persistence: User contexts and personalities are saved between sessions.

Table of Contents

    Installation
        Prerequisites
        Clone the Repository
        Install Dependencies
        Configuration
    Usage
        Running the Bot
        Available Commands

Installation
Prerequisites

    Python 3.6 or higher: Ensure you have Python installed. You can download it from the official website.
    Discord Bot Token: Create a bot on the Discord Developer Portal and get the bot token.
    OpenAI API Key: Sign up for an account at OpenAI and obtain an API key.
    Stability AI API Key: Sign up at Stability AI to get an API key for image generation.

Clone the Repository

git clone https://github.com/Dumbation42/SAM-Pro.git
cd SAM-Pro

Install Dependencies
Option 1: Using the Install Script

Run the provided Python script to install all dependencies automatically.

python install_dependencies.py

Option 2: Using requirements.txt

Alternatively, install dependencies using pip and the provided requirements.txt file.

pip install -r requirements.txt

Configuration

Create a config.json file in the root directory of the project with the following structure:

{
  "OPENAI_API_KEY": "your_openai_api_key",
  "STABLE_API": "your_stability_ai_api_key",
  "BOT_TOKEN": "your_discord_bot_token"
}

    Replace "your_openai_api_key" with your OpenAI API key.
    Replace "your_stability_ai_api_key" with your Stability AI API key.
    Replace "your_discord_bot_token" with your Discord bot token.

Usage
Running the Bot

To start the bot, run the main script:

python bot.py

Available Commands
Slash Commands

    /help: Displays a help message with all available commands.
    /refresh: Clears your conversation context with the bot.
    /style [style]: Sets a custom response style (personality) for the bot.
    /freewill: Lets the bot randomly decide a personality for you.
    /ask [question]: Ask the bot a question.
    /image [prompt]: Generates an image based on the provided prompt.

Direct Interaction

    Mentioning the Bot: You can mention the bot in any channel it's in to start a conversation.

Examples

    Set Personality

/style Wise Mentor

Bot responds:

Your personality has been set to: Wise Mentor

Generate Image

/image A futuristic city skyline at sunset

Bot responds with the generated image or "Generation Refused" if the request is denied.

Ask a Question

/ask What is the capital of France?

Bot responds:

The capital of France is Paris.

Note: This bot uses paid APIs. Monitor your usage on OpenAI and Stability AI platforms to avoid unexpected charges.
