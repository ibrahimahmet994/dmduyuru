import discord
from discord.ext import commands, tasks
import asyncio
import random
import os

# ----------------------
# CONFIG
# ----------------------
BOT_TOKEN = os.getenv("")  # tokeni ortam değişkeninden al
LOG_CHANNEL_ID = 1394835843629318326
INVITE_LINK = "https://discord.gg/jqMFKCyg"
BATCH_SIZE = 10
DM_DELAY_RANGE = (3, 6)
BATCH_DELAY_RANGE = (5, 10)
HOURLY_LIMIT = 100

TARGETS = []  # Bot, sunucudaki komut ile rol ve guild ID otomatik alacak

running = False
sent_users = set()
hourly_count = 0
hour_start = None

# ----------------------
# INTENTS
# ----------------------
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------
# MESAJLARI YÜKLE
# ----------------------
def load_messages():
    with open("messages.txt", "r", encoding="utf-8") as f:
        content = f.read()
    blocks = [m.strip() for m in content.split("\n\n") if m.strip()]
    return blocks

MESSAGES = load_messages()

# ----------------------
# LOG
# ----------------------
async def log(msg):
    ch = bot.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(msg)

# ----------------------
# SAFE DM
# ----------------------
async def safe_dm(user, text):
    global hourly_count, hour_start
    if hour_start is None:
        hour_start = asyncio.get_event_loop().time()

    if hourly_count >= HOURLY_LIMIT:
        await log("⏸ Saatlik limit doldu, 60 dk bekleniyor.")
        await asyncio.sleep(3600)
        hourly_count = 0
        hour_start = asyncio.get_event_loop().time()

    try:
        await user.send(text)
        hourly_count += 1
        await log(f"✅ DM gönderildi: {user}")
        return True
    except Exception as e:
        await log(f"❌ DM atılamadı: {user} | {e}")
        return False

# ----------------------
# BATCH DM
# ----------------------
async def process_all():
    global running
    for target in TARGETS:
        if not running:
            return

        guild = bot.get_guild(target["guild_id"])
        if not guild:
            continue

        role = guild.get_role(target["role_id"])
        if not role:
            continue

        members = [m for m in role.members if not m.bot and m.id not in sent_users]
        random.shuffle(members)
        batch = []

        for member in members:
            if not running:
                return

            batch.append(member)

            if len(batch) >= BATCH_SIZE:
                msg = random.choice(MESSAGES).replace("{link}", INVITE_LINK)
                for m in batch:
                    await safe_dm(m, msg)
                    sent_users.add(m.id)
                    await asyncio.sleep(random.uniform(*DM_DELAY_RANGE))
                batch.clear()
                await asyncio.sleep(random.uniform(*BATCH_DELAY_RANGE))

# ----------------------
# KOMUTLAR
# ----------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def rol_dm(ctx, role: discord.Role):
    """!rol_dm @Rol → otomatik DM başlatır"""
    TARGETS.append({"guild_id": ctx.guild.id, "role_id": role.id})
    await ctx.send(f"✅ DM için rol eklendi: {role.name}")

@bot.command()
@commands.has_permissions(administrator=True)
async def baslat(ctx):
    global running
    if running:
        await ctx.send("⚠️ Bot zaten çalışıyor.")
        return

    running = True

    # İlk DM: Bot sahibi veya komutu atan admin
    try:
        await ctx.author.send("🚀 DM gönderimi BAŞLADI. Bot şu an çalışıyor.")
    except Exception:
        pass

    await ctx.send("🚀 DM gönderimi başlatıldı.")
    await log("🚀 DM gönderimi başlatıldı.")
    bot.loop.create_task(process_all())

@bot.command()
@commands.has_permissions(administrator=True)
async def durdur(ctx):
    global running
    running = False
    await ctx.send("⛔ DM gönderimi durduruldu.")
    await log("⛔ DM gönderimi durduruldu.")

@bot.command()
async def durum(ctx):
    await ctx.send(f"📊 Bot durumu: {'ÇALIŞIYOR' if running else 'DURUYOR'}")
    
    await bot.change_presence(
    status=discord.Status.online,  # idle/online/dnd/invisible
    activity=discord.Game(name="İppoDev")
)


# ----------------------
# AFK GİBİ DURUM
# ----------------------
@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="İppo.Dev"
        )
    )
    print(f"{bot.user} online. !rol_dm ile rol seç, !baslat ile çalıştır.")

# ----------------------
# RUN BOT
# ----------------------
bot.run("")
