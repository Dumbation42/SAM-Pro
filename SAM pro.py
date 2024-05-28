import asyncio
from json import load
from io import BytesIO
from aiosqlite import connect
from asyncio import sleep, run
import openai
from discord.ext.commands import Bot
from aiohttp import ClientSession
from discord import Intents, File, Status, Activity, ActivityType

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
    global db
    db = await connect("database.db")
    async with db.cursor() as cursor:
        await cursor.execute(
            "CREATE TABLE IF NOT EXISTS database(guilds INTEGER, channels INTEGER, models TEXT)"
        )
    await bot.change_presence(
        status=Status.online,
        activity=Activity(
            type=ActivityType.playing,
            name=f"the role of {botpersonality} | SAM Pro v1.0",
        ),
    )
    print(f"{bot.user} has connected to Discord.")

@bot.event
async def on_message(message):
    global server_memory

    if message.author.bot or not message.guild or not bot.user.mentioned_in(message):
        return

    if "c.image" in message.content:
        image_prompt = message.content.replace("c.image", "").strip()
        question_to_gpt35 = f"Is the following prompt likely to generate content that is NSFW? | Prompt: '{image_prompt}'"

        try:
            gpt35_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are being used for an internal check to see if a prompt for a discord bots image generation tool would be considered NSFW."},
                    {"role": "user", "content": question_to_gpt35}
                ]
            )
            content_safe = "no" in gpt35_response.choices[0].message['content'].lower()
        except Exception as e:
            print(f"An error occurred querying GPT-3.5 Turbo: {e}")
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
        global botpersonality
        botpersonality = message.content.split("c.style", 1)[1].strip()
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
        full_prompt = f"{server_last_response} | (Respond in the style of {botpersonality}) | Current Prompt: {prompt}".strip()

        async with message.channel.typing():
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f"You are a discord bot named SAM. You are designed to respond in the style of: {botpersonality}."},
                        {"role": "system", "content": f"Your previous response to this conversation in this server is: {server_last_response}."},
                        {"role": "user", "content": prompt}
                    ]
                )
                server_memory[server_id] = response.choices[0].message['content'].strip()
                await message.channel.send(response.choices[0].message['content'].strip())
            except Exception as e:
                print(f"An error occurred: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    run(init_db())
    bot.run(config["BOT_TOKEN"])
