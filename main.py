import discord
from discord.ext import commands
from notion_client import Client
import openai
import os
import datetime

from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Retrieve environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
greeting_channel_id = int(os.getenv("greeting_channel_id"))

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Make sure to enable message content intent

bot = commands.Bot(command_prefix='!', intents=intents)

client = openai.OpenAI(api_key=OPENAI_API_KEY)
# Initialize Notion client
notion = Client(auth=NOTION_TOKEN)


# Function to format calendar data for OpenAI
def format_calendar_for_openai(calendar_entries):
    return "\n\n".join(calendar_entries)


# Define a command called '!ask'
@bot.command(name='ask')
async def ask(ctx, *, question: str):
    # Fetch the calendar entries first
    try:
        now = datetime.datetime.now()

        response = notion.databases.query(database_id=NOTION_DATABASE_ID)
        calendar_entries = [
            f"{entry['properties']['Name']['title'][0]['plain_text']}: {entry['properties']['Date']['date']['start']} to {entry['properties']['Date']['date']['end']}"
            for entry in response["results"] if entry['properties']['Name']['title']]

        calendar_context = format_calendar_for_openai(calendar_entries)

        # OpenAI conversation
        openai_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a cute and supportive assistant. "
                                              f"Keep responses short. The date is {now}"},
                {"role": "user", "content": calendar_context},
                {"role": "user", "content": question}
            ]
        )

        answer = openai_response.choices[0].message.content
        await ctx.send(answer)

    except Exception as e:
        await ctx.send("Failed to fetch calendar entries or process your question.")
        print(f"Error: {e}")


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


bot.run(DISCORD_TOKEN)