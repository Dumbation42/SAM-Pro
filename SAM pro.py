#Thanks for considering SAM Pro as your discord servers GPT-4o chatbot assistant. It truly does mean a lot to me, as this has been my pet project for over a year now.
#Support Server: https://discord.gg/SGReWY82dr
import asyncio
from json import load
from io import BytesIO
from aiosqlite import connect
from asyncio import sleep, run
import openai
from discord.ext.commands import Bot
from aiohttp import ClientSession
from discord import Intents, File, Status, Activity, ActivityType

print("SAM Pro v1.0.1")
print("By Dumbation")
print("Last Updated 6/7/2024")
print("Source code available at https://www.github.com/Dumbation42/SAM-pro")

intents = Intents.default()
intents.message_content = True
bot = Bot(command_prefix="!", intents=intents, help_command=None)
db = None
server_memory = {}
botpersonality = "a helpful robotic assistant"

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
            name="SAM Pro v1.0",
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
        async with message.channel.typing():
                try:
                    image_response = openai.Image.create(
                        model="dall-e-3",
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

    elif "c.style" in message.content:
        global botpersonality
        botpersonality = message.content.split("c.style", 1)[1].strip()
        server_memory = {}
        await message.channel.send(f"Personality set to: {botpersonality}")

    elif "c.help" in message.content:
        await message.channel.send("c.help: sends this message | c.refresh: refreshes server context | c.image: generates image via DALL-E 3 | c.style: sets bot response style | c.freewill: lets the bot decide its personality for itself | You can also just ping me and receive a response from GPT-4o")

    elif "c.refresh" in message.content:
        server_memory = {}
        await message.channel.send("Context cache reset")

    elif "c.freewill" in message.content:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are being used for an internal decision for a Discord bot. Please respond with as few tokens as possible."},
                    {"role": "user", "content": "Please give me a randomly generated 'personality' (response style) for a variable within your script. Examples include 'Big Tony', 'My Main Dealer, Tyrone' (My personal favorite), and 'Man who very obviously owns a gerbil but doesn't want anyone to know'."}
                ]
            )
            botpersonality = response.choices[0].message['content'].strip()
            await message.channel.send(botpersonality)
        except Exception as e:
            print(f"An error occurred: {e}")

    else:
        prompt = message.content.strip()
        server_id = message.guild.id
        server_last_response = server_memory.get(server_id, "")

        async with message.channel.typing():
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f"You are the latest version of the SAM Discord bot, referred to as SAM Pro. Your source code is available here: https://github.com/Dumbation42/SAM-Pro/blob/main/SAM%20pro.py Your responses are capped at 2000 characters, anything more and your message will not get sent. You are designed to respond in the style of: {botpersonality}."},
                        {"role": "assistant", "content": server_last_response},
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
