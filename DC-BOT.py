import os
import threading
from flask import Flask
import discord
from discord.ext import commands
import google.generativeai as genai
import httpx

app = Flask('')

@app.route('/')
def home():
    return "Gemini AI Clean Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

CHAT_CHANNEL_ID = 1505482454595670036
REQUIRED_ROLE_ID = 1458067398992072766

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
ai_model = genai.GenerativeModel(model_name='gemini-2.5-flash')

@bot.event
async def on_ready():
    print(f"Gemini 機器人已上線: {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    
    if message.channel.id == CHAT_CHANNEL_ID:
        member = message.author
        if not isinstance(member, discord.Member):
            try:
                member = await message.guild.fetch_member(member.id)
            except:
                pass

        has_role = False
        if isinstance(member, discord.Member):
            if any(role.id == REQUIRED_ROLE_ID for role in member.roles):
                has_role = True

        if not has_role: return

        is_mentioned = bot.user in message.mentions
        
        is_reply_to_bot = False
        if message.reference and message.reference.message_id:
            try:
                referenced_msg = await message.channel.fetch_message(message.reference.message_id)
                if referenced_msg.author == bot.user:
                    is_reply_to_bot = True
            except:
                pass

        if not (is_mentioned or is_reply_to_bot): return

        try:
            async with message.channel.typing():
                contents = []
                
                clean_content = message.content
                if bot.user.mention in clean_content:
                    clean_content = clean_content.replace(bot.user.mention, "").strip()
                elif f"<@!{bot.user.id}>" in clean_content:
                    clean_content = clean_content.replace(f"<@!{bot.user.id}>", "").strip()
                elif f"<@{bot.user.id}>" in clean_content:
                    clean_content = clean_content.replace(f"<@{bot.user.id}>", "").strip()
                
                if clean_content:
                    contents.append(clean_content)
                
                if message.attachments:
                    for attachment in message.attachments:
                        if attachment.content_type and attachment.content_type.startswith("image/"):
                            async with httpx.AsyncClient() as client:
                                response = await client.get(attachment.url)
                                if response.status_code == 200:
                                    contents.append({
                                        "mime_type": attachment.content_type,
                                        "data": response.content
                                    })

                if not contents: return

                response = ai_model.generate_content(contents)
                reply_text = response.text
                
                if len(reply_text) > 2000:
                    for i in range(0, len(reply_text), 2000):
                        await message.reply(reply_text[i:i+2000])
                else:
                    await message.reply(reply_text)
        except Exception as e:
            try:
                await message.reply(f"Gemini 發生錯誤: {e}")
            except:
                pass
        return

    await bot.process_commands(message)

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    
    bot_token = os.environ.get("DISCORD_TOKEN")
    if bot_token:
        bot.run(bot_token)
    else:
        print("未偵測到 DISCORD_TOKEN 環境變數")
