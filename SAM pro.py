import asyncio
import signal
from os import remove
from json import load
from io import BytesIO
from aiosqlite import connect
from asyncio import sleep, run
import openai
from discord.ui import Button, View
from discord.ext.commands import Bot
from aiohttp import ClientSession, ClientError
from discord import Intents, Embed, File, Status, Activity, ActivityType, Colour
from discord.app_commands import (
    describe,
    checks,
    BotMissingPermissions,
    MissingPermissions,
    CommandOnCooldown,
)

intents = Intents.default()
intents.message_content = True
bot = Bot(command_prefix="!", intents=intents, help_command=None)
db = None
server_memory = {}
textCompModels = ["gpt-4o"]
imageGenModels = ["dall-e-3"]
botpersonality = "a helpful robotic assistant"

# Initialize OpenAI API key
with open("config.json", "r") as file:
    config = load(file)
openai.api_key = config["OPENAI_API_KEY"]

async def init_db():
    return await connect("database.db")

@bot.event
async def on_ready():
    print(f"\033[1;94m INFO \033[0m| {bot.user} has connected to Discord.")
    global db
    db = await connect("database.db")
    async with db.cursor() as cursor:
        await cursor.execute(
            "CREATE TABLE IF NOT EXISTS database(guilds INTEGER, channels INTEGER, models TEXT)"
        )
    print("\033[1;94m INFO \033[0m| Database connection successful.")
    sync_commands = await bot.tree.sync()
    while True:
        await bot.change_presence(
            status=Status.online,
            activity=Activity(
                type=ActivityType.playing,
                name=f"the role of {botpersonality} | SAM Pro v1.0",
            ),
        )
        await sleep(1)

@bot.event
async def on_message(message):
    global server_memory

    if message.author.bot:
        return

    if not message.guild or message.content.startswith('!'):
        return

    if not bot.user.mentioned_in(message):
        return

    if "c.image" in message.content:
        server_id = message.guild.id
        image_prompt = message.content.replace("c.image", "").strip()
        question_to_gpt4 = f"This is an automated prompt used for an AI moderated blacklist for an image generator. Please respond with 'yes' or 'no': Is the following prompt likely to generate content that is considered NSFW (Pornographic Content or Nudity)? | Prompt: '{image_prompt}'"

        try:
            gpt4_response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": question_to_gpt4}
                ]
            )
            content_safe = "no" in gpt4_response.choices[0].message['content'].lower()
        except Exception as e:
            print(f"An error occurred querying GPT-4o: {e}")
            content_safe = False

        if content_safe:
            async with message.channel.typing():
                try:
                    image_response = openai.Image.create(
                        prompt=image_prompt,
                        n=1,
                        size="1024x1024"
                    )
                    image_url = image_response['data'][0]['url']

                    async with ClientSession() as session:
                        async with session.get(image_url) as resp:
                            if resp.status != 200:
                                return await message.channel.send("Could not download image.")
                            data = BytesIO(await resp.read())
                            await message.channel.send(file=File(data, 'generated_image.png'))
                except Exception as e:
                    print(f"An error occurred generating image: {e}")
        else:
            await message.channel.send("I just don't feel up to the task right now.")

    elif "c.style" in message.content:
        parts = message.content.split("c.style", 1)
        if len(parts) > 1:
            global botpersonality
            botpersonality = parts[1].strip()
            server_memory = {}
            await message.channel.send(f"Personality Set To: {botpersonality}")
    
    elif "c.help" in message.content:
        await message.channel.send("c.help: sends this message | c.refresh: refreshes server context | c.image: generates image via DALL-E 3 | c.style: sets bot response style | You can also just ping me and receive a response from GPT-4o")

    elif "c.refresh" in message.content:
        server_memory = {}
        await message.channel.send("Context Cache Reset")

    else:
        prompt = message.content.strip()
        server_id = message.guild.id
        server_last_response = server_memory.get(server_id, "")
        full_prompt = f"GPT-4o Last Response: {server_last_response} |  (Ignore '@Bot User ID Here') (Respond in the style of {botpersonality}) | Current Prompt: {prompt}".strip()

        async with message.channel.typing():
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": full_prompt}
                    ]
                )
                server_memory[server_id] = response.choices[0].message['content'].strip()
                await message.channel.send(response.choices[0].message['content'].strip())
            except Exception as e:
                print(f"An error occurred: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(config["BOT_TOKEN"])
