import os
from collections import defaultdict

import discord
from discord.ext import commands

# ===== CẤU HÌNH =====
TOKEN = os.getenv("TOKEN")
WELCOME_CHANNEL_ID = 1488428612087447665  # đổi nếu cần

# ===== INTENTS =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== DATA TẠM =====
spam = defaultdict(int)
levels = defaultdict(int)

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
        title="Chào mừng thành viên mới 🎉",
        description=(
            f"Xin chào {member.mention} đến với server!\n"
            f"Chúc bạn chơi vui vẻ 💜"
        ),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await channel.send(embed=embed)

    role = discord.utils.get(member.guild.roles, name="Member")
    if role:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            print("❌ Bot không đủ quyền để thêm role Member.")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    user_id = message.author.id

    # chống spam đơn giản
    spam[user_id] += 1
    if spam[user_id] > 5:
        try:
            await message.delete()
            await message.channel.send(f"🚫 {message.author.mention} spam quá nhiều!")
        except discord.Forbidden:
            pass
        return

    # auto reply
    content = message.content.lower()
    keywords = ["tải game", "link tải", "download", "link", "tải ở đâu"]
    if any(keyword in content for keyword in keywords):
        await message.reply("📥 Link tải game có tại kênh #download nhé!")

    # level đơn giản
    levels[user_id] += 1
    if levels[user_id] % 10 == 0:
        await message.channel.send(
            f"🎉 {message.author.mention} đã lên level {levels[user_id] // 10}!"
        )

    await bot.process_commands(message)


# ===== PREFIX COMMANDS =====
@bot.command()
async def ping(ctx: commands.Context):
    await ctx.send("Pong! 🏓")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx: commands.Context, amount: int):
    if amount <= 0:
        await ctx.send("❌ Số lượng tin nhắn phải lớn hơn 0.")
        return

    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Đã xóa {amount} tin nhắn.")
    await msg.delete(delay=3)


@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx: commands.Context, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role is None:
        await ctx.send("❌ Không tìm thấy role Muted.")
        return

    try:
        await member.add_roles(role)
        await ctx.send(f"🔇 {member.mention} đã bị mute!")
    except discord.Forbidden:
        await ctx.send("❌ Bot không đủ quyền để thêm role này.")


@bot.command()
async def info(ctx: commands.Context, member: discord.Member = None):
    member = member or ctx.author
    joined = member.joined_at.strftime("%d/%m/%Y %H:%M:%S") if member.joined_at else "Không rõ"
    created = member.created_at.strftime("%d/%m/%Y %H:%M:%S")

    embed = discord.Embed(title="Thông tin thành viên 👤")
    embed.add_field(name="Tên", value=str(member), inline=False)
    embed.add_field(name="ID", value=str(member.id), inline=False)
    embed.add_field(name="Tạo tài khoản", value=created, inline=False)
    embed.add_field(name="Tham gia server", value=joined, inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx: commands.Context, member: discord.Member, *, reason="Không có lý do"):
    if member == ctx.author:
        await ctx.send("❌ Bạn không thể tự kick chính mình.")
        return

    if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        await ctx.send("❌ Bạn không thể kick người có role cao hơn hoặc bằng bạn.")
        return

    try:
        await member.kick(reason=reason)
        await ctx.send(f"👢 Đã kick {member.mention} | Lý do: {reason}")
    except discord.Forbidden:
        await ctx.send("❌ Bot không đủ quyền để kick thành viên này.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi khi kick: {e}")


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx: commands.Context, member: discord.Member, *, reason="Không có lý do"):
    if member == ctx.author:
        await ctx.send("❌ Bạn không thể tự ban chính mình.")
        return

    if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        await ctx.send("❌ Bạn không thể ban người có role cao hơn hoặc bằng bạn.")
        return

    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 Đã ban {member.mention} | Lý do: {reason}")
    except discord.Forbidden:
        await ctx.send("❌ Bot không đủ quyền để ban thành viên này.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi khi ban: {e}")


# ===== SLASH COMMAND =====
@bot.tree.command(name="hello", description="Chào người dùng")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Xin chào {interaction.user.mention} 👋")


# ===== ERROR HANDLER =====
@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bạn không có quyền dùng lệnh này.")
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Thiếu tham số.")
        return

    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ Sai định dạng tham số.")
        return

    await ctx.send(f"❌ Có lỗi xảy ra: {error}")

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name="Member")

    if role:
        try:
            await member.add_roles(role)
            print(f"Đã gán role cho {member}")
        except discord.Forbidden:
            print("Bot không đủ quyền")
    else:
        print("Không tìm thấy role")


# ===== RUN =====
if not TOKEN:
    raise RuntimeError("Thiếu biến môi trường TOKEN")

bot.run(TOKEN)
