import os
import threading
from flask import Flask
import discord
from discord.ext import commands
from openai import OpenAI

app = Flask('')

@app.route('/')
def home():
    return "DeepSeek AI Multi-Modal Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

CHAT_CHANNEL_ID = 1505482454595670036
REQUIRED_ROLE_ID = 1458067398992072766

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

ai_client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

@bot.event
async def on_ready():
    print(f"DeepSeek 機器人已上線: {bot.user.name}")

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

        try:
            async with message.channel.typing():
                content_list = [{"type": "text", "text": message.content}]
                
                if message.attachments:
                    for attachment in message.attachments:
                        if attachment.content_type and attachment.content_type.startswith("image/"):
                            content_list.append({
                                "type": "image_url",
                                "image_url": {"url": attachment.url}
                            })

                response = ai_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "user", "content": content_list}
                    ],
                    stream=False
                )
                reply_text = response.choices[0].message.content
                
                if len(reply_text) > 2000:
                    for i in range(0, len(reply_text), 2000):
                        await message.reply(reply_text[i:i+2000])
                else:
                    await message.reply(reply_text)
        except Exception as e:
            try:
                await message.reply(f"DeepSeek 處理發生錯誤: {e}")
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
