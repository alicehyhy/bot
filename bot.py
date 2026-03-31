import os
import discord
from discord.ext import commands

# ===== CẤU HÌNH =====
TOKEN = os.getenv("MTQ4ODQwODEwOTk1MjAxMjI4OA.G7vDP5.owFRrkzIj1RR9UT8qp6phABp-GD2MxtdNvonuo")  # ✅ SỬA Ở ĐÂY

WELCOME_CHANNEL_ID = 1488428612087447665  # ID kênh chào mừng

# ===== INTENTS =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

spam = {}
levels = {}

# ===== SỰ KIỆN =====
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Bot online: {bot.user}")
        print(f"✅ Đã sync {len(synced)} slash command")
    except Exception as e:
        print(f"❌ Lỗi sync slash command: {e}")

@bot.event
async def on_member_join(member: discord.Member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)

    if channel is None:
        print("❌ Không tìm thấy kênh chào mừng.")
        return

    embed = discord.Embed(
        title="Chào mừng 🎉",
        description=f"Xin chào {member.mention} đến với server 💜"
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await channel.send(embed=embed)

    role = discord.utils.get(member.guild.roles, name="Member")
    if role:
        await member.add_roles(role)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user = message.author.id

    # chống spam
    spam[user] = spam.get(user, 0) + 1
    if spam[user] > 5:
        await message.delete()
        await message.channel.send(f"🚫 {message.author.mention} spam!")
        return

    # auto reply
    if any(k in message.content.lower() for k in ["link", "tải", "download"]):
        await message.reply("📥 Link ở kênh #download nhé!")

    # level
    levels[user] = levels.get(user, 0) + 1
    if levels[user] % 10 == 0:
        await message.channel.send(
            f"🎉 {message.author.mention} level {levels[user]//10}"
        )

    await bot.process_commands(message)

# ===== COMMAND =====
@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

@bot.tree.command(name="hello", description="Chào")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}")

# ===== RUN =====
if not TOKEN:
    raise RuntimeError("Thiếu biến môi trường TOKEN")

bot.run(TOKEN)