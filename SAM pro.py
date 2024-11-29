import openai
import json
from io import BytesIO
import requests
import discord
from discord.ext import commands
from discord import Intents, File, Status, Activity, ActivityType
import os

# -------------------------
# Configuration and Setup
# -------------------------

# Load API keys and bot token from the configuration file
with open("config.json", "r") as file:
    config = json.load(file)

# Set OpenAI and Stability AI API keys
openai.api_key = config["OPENAI_API_KEY"]
stable_api_key = config["STABLE_API"]

# Initialize the Discord bot with appropriate intents
intents = Intents.default()
intents.message_content = True  # Enable access to message content
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Access to the bot's application command tree (for slash commands)
tree = bot.tree

# -------------------------
# User Data Management
# -------------------------

# Dictionaries to store per-user contexts and personalities
user_contexts = {}
user_personalities = {}


def load_user_data():
    """
    Loads user contexts and personalities from disk into memory.
    If the files do not exist or are corrupted, initializes empty dictionaries.
    """
    global user_contexts, user_personalities

    # Load user contexts
    if os.path.exists("context.txt"):
        try:
            with open("context.txt", "r") as f:
                user_contexts = json.load(f)
        except json.JSONDecodeError:
            user_contexts = {}
    else:
        user_contexts = {}

    # Load user personalities
    if os.path.exists("personality.txt"):
        try:
            with open("personality.txt", "r") as f:
                user_personalities = json.load(f)
        except json.JSONDecodeError:
            user_personalities = {}
    else:
        user_personalities = {}


def save_user_data():
    """
    Saves user contexts and personalities from memory to disk.
    """
    # Save user contexts
    with open("context.txt", "w") as f:
        json.dump(user_contexts, f)

    # Save user personalities
    with open("personality.txt", "w") as f:
        json.dump(user_personalities, f)


# -------------------------
# Bot Events
# -------------------------

@bot.event
async def on_ready():
    """
    Event handler for when the bot is ready and connected to Discord.
    Loads user data, sets the bot's presence, and syncs slash commands.
    """
    load_user_data()  # Load user contexts and personalities from disk

    # Set the bot's status and activity
    await bot.change_presence(
        status=Status.online,
        activity=Activity(
            type=ActivityType.playing,
            name="freakmode1",  # Custom status message
        ),
    )

    # Sync the slash commands with Discord
    await tree.sync()
    print(f"{bot.user} has connected to Discord.")


@bot.event
async def on_message(message):
    """
    Event handler for incoming messages.
    Processes commands and handles mentions for direct interactions.
    """
    if message.author.bot:
        # Ignore messages from bots to prevent loops
        return

    # Process any commands in the message
    await bot.process_commands(message)

    # If the bot is mentioned in the message or it's a DM, respond
    if message.guild is None or bot.user.mentioned_in(message):
        user_id_str = str(message.author.id)

        # Retrieve the user's last context and personality
        prompt = message.content.strip()
        user_last_response = user_contexts.get(user_id_str, "")
        user_personality = user_personalities.get(user_id_str, "a helpful assistant")

        # Indicate that the bot is typing a response
        async with message.channel.typing():
            try:
                # Generate a response using OpenAI's ChatCompletion
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are the latest version of godck. "
                                "Your responses are capped at 2000 characters. "
                                f"You are designed to respond in the style of: {user_personality}."
                            ),
                        },
                        {"role": "assistant", "content": user_last_response},
                        {"role": "user", "content": prompt},
                    ],
                )

                # Extract the assistant's reply
                bot_response = response.choices[0]['message']['content'].strip()

                # Update the user's context with the new response
                user_contexts[user_id_str] = bot_response
                save_user_data()  # Save updated contexts to disk

                # Send the response to the user, ensuring it doesn't exceed Discord's character limit
                await message.channel.send(bot_response[:2000])
            except Exception as e:
                print(f"An error occurred: {e}")
                await message.channel.send(f"Error in generating response: {str(e)}")


# -------------------------
# Slash Commands
# -------------------------

@tree.command(name='help', description='Displays help message.')
async def show_help(interaction: discord.Interaction):
    """
    Sends a help message to the user, detailing available commands.
    """
    help_message = (
        "/help: Shows this help message.\n"
        "/refresh: Refreshes your context.\n"
        "/image [prompt]: Generates an image via Stable Diffusion XL.\n"
        "/style [style]: Sets your bot response style.\n"
        "/freewill: Lets the bot decide its personality for you.\n"
        "/ask [question]: Ask the bot a question.\n"
        "You can also mention me and receive a response."
    )
    await interaction.response.send_message(help_message)


@tree.command(name='refresh', description='Refreshes your context.')
async def refresh_context(interaction: discord.Interaction):
    """
    Clears the user's conversation context, effectively starting a new conversation.
    """
    user_id_str = str(interaction.user.id)
    user_contexts[user_id_str] = ""  # Reset the user's context
    save_user_data()  # Save changes to disk
    await interaction.response.send_message("Your context cache has been reset.")


@tree.command(name='style', description='Sets your bot response style.')
async def set_style(interaction: discord.Interaction, style: str):
    """
    Sets the user's preferred response style or 'personality' for the bot.
    """
    user_id_str = str(interaction.user.id)
    user_personalities[user_id_str] = style.strip()  # Update the user's personality
    save_user_data()  # Save changes to disk
    await interaction.response.send_message(f"Your personality has been set to: {style.strip()}")


@tree.command(name='freewill', description='Bot decides its personality for you.')
async def free_will(interaction: discord.Interaction):
    """
    Allows the bot to randomly generate a personality for the user.
    """
    user_id_str = str(interaction.user.id)
    await interaction.response.defer()  # Defer the response as it may take time

    try:
        # Request OpenAI to generate a random personality
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are being used for an internal decision for a Discord bot. "
                        "Please respond with as few tokens as possible."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Please give me a randomly generated 'personality' "
                        "(response style) for a variable within your script. "
                        "Examples include 'Big Tony', 'My Main Dealer, Tyrone', "
                        "and 'Man who very obviously owns a gerbil but doesn't want anyone to know'."
                    ),
                },
            ],
        )

        # Extract the generated personality
        personality = response.choices[0]['message']['content'].strip()

        # Update the user's personality
        user_personalities[user_id_str] = personality
        save_user_data()  # Save changes to disk

        await interaction.followup.send(f"Your new personality is: {personality}")
    except Exception as e:
        print(f"An error occurred: {e}")
        await interaction.followup.send(f"Error in generating personality: {str(e)}")


@tree.command(name='ask', description='Ask the bot a question.')
async def ask_command(interaction: discord.Interaction, question: str):
    """
    Allows the user to ask a question to the bot and receive a response.
    """
    user_id_str = str(interaction.user.id)
    user_last_response = user_contexts.get(user_id_str, "")
    user_personality = user_personalities.get(user_id_str, "a helpful assistant")

    await interaction.response.defer()  # Defer the response as it may take time

    try:
        # Generate a response using OpenAI's ChatCompletion
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the latest version of godck. "
                        "Your responses are capped at 2000 characters. "
                        f"You are designed to respond in the style of: {user_personality}."
                    ),
                },
                {"role": "assistant", "content": user_last_response},
                {"role": "user", "content": question},
            ],
        )

        # Extract the assistant's reply
        bot_response = response.choices[0]['message']['content'].strip()

        # Update the user's context with the new response
        user_contexts[user_id_str] = bot_response
        save_user_data()  # Save updated contexts to disk

        # Send the response to the user, ensuring it doesn't exceed Discord's character limit
        await interaction.followup.send(bot_response[:2000])
    except Exception as e:
        print(f"An error occurred: {e}")
        await interaction.followup.send(f"Error in generating response: {str(e)}")


@tree.command(name='image', description='Generates an image via Stable Diffusion XL.')
async def generate_image(interaction: discord.Interaction, prompt: str):
    """
    Generates an image based on the user's prompt using Stable Diffusion XL.
    If the API returns a 403 error, informs the user with "Generation Refused".
    """
    await interaction.response.defer()  # Defer the response as it may take time

    try:
        # Prepare form data for the API request
        form_data = {
            'prompt': (None, prompt.strip()),
            'output_format': (None, 'jpeg'),
        }

        # Make a POST request to Stability AI's API
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/ultra",
            headers={
                "authorization": f"Bearer {stable_api_key}",
                "accept": "image/*",
            },
            files=form_data,  # Send data as multipart/form-data
        )

        if response.status_code == 200:
            # If the request was successful, send the image to the user
            image_data = BytesIO(response.content)
            file = File(image_data, 'generated_image.jpeg')
            await interaction.followup.send(file=file)
        elif response.status_code == 403:
            # If the API returns a 403 error, inform the user with "Generation Refused"
            print(f"API request returned 403 Forbidden.")
            await interaction.followup.send("Generation Refused")
        else:
            # For other errors, log the error and inform the user
            error_message = response.json()
            print(f"API request failed with status {response.status_code}: {error_message}")
            await interaction.followup.send(f"Failed to generate image. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while generating the image: {e}")
        await interaction.followup.send(f"Error generating image: {str(e)}")


# -------------------------
# Main Execution
# -------------------------

if __name__ == "__main__":
    # Start the bot using the token from the configuration file
    bot.run(config["BOT_TOKEN"])
