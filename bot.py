import os
from collections import defaultdict

import discord
from discord.ext import commands

# ===== CẤU HÌNH =====
TOKEN = os.getenv("TOKEN")
WELCOME_CHANNEL_ID = 1488428612087447665

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
        print(f"✅ ID kênh welcome đang dùng: {WELCOME_CHANNEL_ID}")
    except Exception as e:
        print(f"❌ Lỗi sync slash command: {e}")


@bot.event
async def on_member_join(member: discord.Member):
    print(f"📥 Thành viên mới vào: {member} ({member.id})")

    # Lấy kênh chào mừng
    channel = bot.get_channel(WELCOME_CHANNEL_ID)

    # Nếu cache chưa có thì fetch trực tiếp
    if channel is None:
        try:
            channel = await bot.fetch_channel(WELCOME_CHANNEL_ID)
        except Exception as e:
            print(f"❌ Không tìm thấy kênh chào mừng: {e}")
            channel = None

    # Gửi tin nhắn chào mừng
    if channel is not None:
        embed = discord.Embed(
            title="Chào mừng thành viên mới 🎉",
            description=(
                f"Xin chào {member.mention} đến với server!\n"
                f"Chúc bạn chơi vui vẻ 💜"
            ),
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"User ID: {member.id}")

        try:
            await channel.send(embed=embed)
            print("✅ Đã gửi tin nhắn chào mừng.")
        except discord.Forbidden:
            print("❌ Bot không có quyền gửi tin nhắn hoặc embed ở kênh welcome.")
        except Exception as e:
            print(f"❌ Lỗi gửi welcome: {e}")
    else:
        print("❌ Channel welcome vẫn là None.")

    # Tự động add role Member
    role = discord.utils.get(member.guild.roles, name="Member")
    if role:
        try:
            await member.add_roles(role, reason="Auto role khi vào server")
            print(f"✅ Đã gán role Member cho {member}")
        except discord.Forbidden:
            print("❌ Bot không đủ quyền để thêm role Member.")
        except Exception as e:
            print(f"❌ Lỗi add role: {e}")
    else:
        print("❌ Không tìm thấy role 'Member'")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    user_id = message.author.id

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

    embed = discord.Embed(title="Thông tin thành viên 👤", color=discord.Color.blurple())
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
        await ctx.send("❌ Bạn không thể ban chính mình.")
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


@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx: commands.Context, *, message: str):
    try:
        await ctx.message.delete()  # 🔥 xóa tin nhắn lệnh
    except:
        pass  # tránh crash nếu thiếu quyền

    await ctx.send(message)  # gửi tin nhắn

# ===== RUN =====
if not TOKEN:
    raise RuntimeError("Thiếu biến môi trường TOKEN")

bot.run(TOKEN)
