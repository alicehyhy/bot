import os
import asyncio
import random
from datetime import timedelta
from collections import defaultdict

import discord
from discord.ext import commands

TOKEN = os.getenv("TOKEN")
WELCOME_CHANNEL_ID = 1488428612087447665

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

spam = defaultdict(int)
levels = defaultdict(int)
giveaways = {}


class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id: str):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id

    @discord.ui.button(
        label="Tham gia",
        emoji="🎉",
        style=discord.ButtonStyle.green,
        custom_id="join_giveaway"
    )
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = giveaways.get(self.giveaway_id)

        if not data:
            await interaction.response.send_message(
                "❌ Giveaway này không còn tồn tại.",
                ephemeral=True
            )
            return

        if interaction.user.bot:
            await interaction.response.send_message(
                "❌ Bot không thể tham gia giveaway.",
                ephemeral=True
            )
            return

        if interaction.user.id in data["participants"]:
            await interaction.response.send_message(
                "⚠️ Bạn đã tham gia giveaway này rồi!",
                ephemeral=True
            )
            return

        data["participants"].add(interaction.user.id)
        await interaction.response.send_message(
            "✅ Bạn đã tham gia giveaway thành công!",
            ephemeral=True
        )


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Bot online: {bot.user}")
        print(f"✅ Đã sync {len(synced)} slash command")
        print(f"✅ ID kênh welcome đang dùng: {WELCOME_CHANNEL_ID}")

        # đăng ký lại view cho button sau khi bot restart
        bot.add_view(GiveawayView("persistent_giveaway_view"))

    except Exception as e:
        print(f"❌ Lỗi sync slash command: {e}")


@bot.event
async def on_member_join(member: discord.Member):
    print(f"📥 Thành viên mới vào: {member} ({member.id})")
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(WELCOME_CHANNEL_ID)
        except Exception as e:
            print(f"❌ Không tìm thấy kênh chào mừng: {e}")
            channel = None

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

    content = message.content.lower()
    keywords = ["tải game", "link tải", "download", "link", "tải ở đâu"]
    if any(keyword in content for keyword in keywords):
        await message.reply("📥 Link tải game có tại kênh #download nhé!")

    levels[user_id] += 1
    if levels[user_id] % 10 == 0:
        await message.channel.send(
            f"🎉 {message.author.mention} đã lên level {levels[user_id] // 10}!"
        )

    await bot.process_commands(message)


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


@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx: commands.Context, *, message: str):
    try:
        await ctx.message.delete()
    except:
        pass

    await ctx.send(message)


@bot.command()
@commands.has_permissions(administrator=True)
async def gstart(ctx: commands.Context, minutes: int, winners: int, *, prize: str):
    try:
        await ctx.message.delete()
    except:
        pass

    if minutes <= 0:
        msg = await ctx.send("❌ Số phút phải lớn hơn 0.")
        await msg.delete(delay=5)
        return

    if winners <= 0:
        msg = await ctx.send("❌ Số người thắng phải lớn hơn 0.")
        await msg.delete(delay=5)
        return

    end_time = discord.utils.utcnow() + timedelta(minutes=minutes)

    embed = discord.Embed(
        title="🎉 GIVEAWAY 🎉",
        description=(
            f"**Phần thưởng:** {prize}\n"
            f"**Số người thắng:** {winners}\n"
            f"**Kết thúc sau:** {minutes} phút\n\n"
            f"Nhấn nút **Tham gia** bên dưới để tham gia!"
        ),
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Host: {ctx.author}")
    embed.timestamp = end_time

    msg = await ctx.send(embed=embed)
    giveaway_id = str(msg.id)

    giveaways[giveaway_id] = {
        "channel_id": ctx.channel.id,
        "message_id": msg.id,
        "prize": prize,
        "winner_count": winners,
        "participants": set(),
        "host_id": ctx.author.id
    }

    await msg.edit(view=GiveawayView(giveaway_id))

    await asyncio.sleep(minutes * 60)

    data = giveaways.get(giveaway_id)
    if not data:
        return

    participants = list(data["participants"])

    if len(participants) == 0:
        end_embed = discord.Embed(
            title="🎉 GIVEAWAY KẾT THÚC",
            description=f"**Quà:** {prize}\n\n❌ Không có ai tham gia.",
            color=discord.Color.red()
        )
        await msg.edit(embed=end_embed, view=None)
        await ctx.send(f"🎉 Giveaway **{prize}** đã kết thúc, nhưng không có ai tham gia.")
        giveaways.pop(giveaway_id, None)
        return

    actual_winners = min(winners, len(participants))
    winner_ids = random.sample(participants, actual_winners)
    mentions = ", ".join(f"<@{user_id}>" for user_id in winner_ids)

    end_embed = discord.Embed(
        title="🎉 GIVEAWAY KẾT THÚC",
        description=(
            f"**Quà:** {prize}\n"
            f"**Người thắng:** {mentions}"
        ),
        color=discord.Color.green()
    )
    end_embed.set_footer(text=f"Tổ chức bởi {ctx.author}")

    await msg.edit(embed=end_embed, view=None)
    await ctx.send(f"🎊 Chúc mừng {mentions} đã thắng giveaway **{prize}**!")

    giveaways.pop(giveaway_id, None)


@bot.command()
@commands.has_permissions(administrator=True)
async def greroll(ctx: commands.Context, message_id: int):
    try:
        await ctx.message.delete()
    except:
        pass

    data = giveaways.get(str(message_id))

    if not data:
        msg = await ctx.send("❌ Không tìm thấy giveaway đang lưu hoặc giveaway đã kết thúc.")
        await msg.delete(delay=5)
        return

    participants = list(data["participants"])
    if not participants:
        msg = await ctx.send("❌ Giveaway này không có ai tham gia.")
        await msg.delete(delay=5)
        return

    winner_id = random.choice(participants)
    await ctx.send(f"🔄 Reroll giveaway **{data['prize']}**: chúc mừng <@{winner_id}>!")


@bot.tree.command(name="hello", description="Chào người dùng")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Xin chào {interaction.user.mention} 👋")


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


if not TOKEN:
    raise RuntimeError("Thiếu biến môi trường TOKEN")

bot.run(TOKEN)
