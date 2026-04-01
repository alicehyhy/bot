import os
import json
import asyncio
import random
from pathlib import Path
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

TF_SAVE_FILE = Path("tf_data.json")
tf_players = {}


def load_tf_data():
    global tf_players
    if TF_SAVE_FILE.exists():
        try:
            with open(TF_SAVE_FILE, "r", encoding="utf-8") as f:
                tf_players = json.load(f)
        except Exception as e:
            print(f"❌ Lỗi load tf_data.json: {e}")
            tf_players = {}
    else:
        tf_players = {}


def save_tf_data():
    try:
        with open(TF_SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(tf_players, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Lỗi save tf_data.json: {e}")


def get_player(user_id: int):
    return tf_players.get(str(user_id))


def get_mood_text(affection: int, energy: int):
    if energy <= 1:
        return "Mệt"
    if affection >= 50:
        return "Rất vui"
    if affection >= 25:
        return "Vui"
    if affection >= 10:
        return "Bình thường"
    return "Buồn"


def ensure_daily(player: dict):
    current_day = player["day"]
    if player.get("daily_day") != current_day:
        player["daily_day"] = current_day
        player["daily_done"] = False
        player["daily_target"] = random.choice(["talk", "feed", "rest"])
        player["daily_reward"] = random.randint(2, 5)


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
        load_tf_data()
        synced = await bot.tree.sync()
        print(f"✅ Bot online: {bot.user}")
        print(f"✅ Đã sync {len(synced)} slash command")
        print(f"✅ ID kênh welcome đang dùng: {WELCOME_CHANNEL_ID}")
        print("✅ Đã load dữ liệu mini game Teaching Feeling")

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


@bot.group(invoke_without_command=True)
async def tf(ctx: commands.Context):
    await ctx.send(
        "📖 Lệnh game: `!tf start`, `!tf status`, `!tf talk`, `!tf feed`, `!tf rest`, `!tf sleep`, `!tf nextday`, `!tf daily`, `!tf reset`"
    )


@tf.command()
async def start(ctx: commands.Context):
    user_id = str(ctx.author.id)

    if user_id in tf_players:
        await ctx.send("⚠️ Bạn đã bắt đầu mini game rồi.")
        return

    tf_players[user_id] = {
        "name": str(ctx.author),
        "day": 1,
        "affection": 0,
        "food": 5,
        "energy": 5,
        "mood": "Buồn",
        "daily_day": 1,
        "daily_done": False,
        "daily_target": random.choice(["talk", "feed", "rest"]),
        "daily_reward": 3
    }
    save_tf_data()

    embed = discord.Embed(
        title="🌱 Bắt đầu câu chuyện",
        description=(
            f"{ctx.author.mention} đã bắt đầu chăm sóc Sylvie.\n"
            f"Ngày 1 bắt đầu."
        ),
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)


@tf.command()
async def status(ctx: commands.Context):
    player = get_player(ctx.author.id)
    if not player:
        await ctx.send("❌ Bạn chưa bắt đầu. Dùng `!tf start`")
        return

    ensure_daily(player)
    player["mood"] = get_mood_text(player["affection"], player["energy"])
    save_tf_data()

    daily_text = "✅ Đã hoàn thành" if player["daily_done"] else f"Chưa xong: `{player['daily_target']}`"

    embed = discord.Embed(
        title="📊 Trạng thái Sylvie",
        description="Một ngày yên bình trong căn nhà nhỏ.",
        color=discord.Color.purple()
    )
    embed.add_field(name="🏠 Day", value=player["day"], inline=True)
    embed.add_field(name="❤️ Affection", value=player["affection"], inline=True)
    embed.add_field(name="💔 Mood", value=player["mood"], inline=True)
    embed.add_field(name="🍞 Food", value=player["food"], inline=True)
    embed.add_field(name="😴 Energy", value=player["energy"], inline=True)
    embed.add_field(name="🎁 Daily", value=daily_text, inline=False)

    await ctx.send(embed=embed)


@tf.command()
async def daily(ctx: commands.Context):
    player = get_player(ctx.author.id)
    if not player:
        await ctx.send("❌ Bạn chưa bắt đầu. Dùng `!tf start`")
        return

    ensure_daily(player)
    save_tf_data()

    target_map = {
        "talk": "Nói chuyện với Sylvie",
        "feed": "Cho Sylvie ăn",
        "rest": "Để Sylvie nghỉ ngơi"
    }

    status = "✅ Đã hoàn thành" if player["daily_done"] else "⌛ Chưa hoàn thành"

    await ctx.send(
        f"🎁 Daily ngày {player['day']}:\n"
        f"• Nhiệm vụ: **{target_map[player['daily_target']]}**\n"
        f"• Thưởng: **+{player['daily_reward']} affection**\n"
        f"• Trạng thái: {status}"
    )


@tf.command()
async def feed(ctx: commands.Context):
    player = get_player(ctx.author.id)
    if not player:
        await ctx.send("❌ Dùng `!tf start` trước.")
        return

    if player["food"] <= 0:
        await ctx.send("❌ Hết đồ ăn rồi.")
        return

    player["food"] -= 1
    gain = random.randint(1, 3)
    player["affection"] += gain
    player["mood"] = get_mood_text(player["affection"], player["energy"])

    text = random.choice([
        f"🍞 Sylvie nhận bữa ăn nhỏ và khẽ gật đầu. (+{gain} affection)",
        f"🍲 Sylvie ăn chậm rãi rồi nhìn bạn dịu hơn. (+{gain} affection)",
        f"🥖 Không khí trở nên ấm áp hơn một chút. (+{gain} affection)"
    ])

    if not player["daily_done"] and player["daily_target"] == "feed":
        player["daily_done"] = True
        player["affection"] += player["daily_reward"]
        text += f"\n🎁 Hoàn thành daily! (+{player['daily_reward']} affection)"

    save_tf_data()
    await ctx.send(text)


@tf.command()
async def rest(ctx: commands.Context):
    player = get_player(ctx.author.id)
    if not player:
        await ctx.send("❌ Dùng `!tf start` trước.")
        return

    gain = random.randint(2, 3)
    player["energy"] = min(player["energy"] + gain, 10)
    player["mood"] = get_mood_text(player["affection"], player["energy"])

    text = random.choice([
        "😴 Sylvie nghỉ ngơi trong yên tĩnh.",
        "🛏️ Căn phòng lặng đi, chỉ còn nhịp thở đều đều.",
        "🌙 Một khoảng nghỉ ngắn khiến tâm trạng ổn hơn."
    ])

    if not player["daily_done"] and player["daily_target"] == "rest":
        player["daily_done"] = True
        player["affection"] += player["daily_reward"]
        text += f"\n🎁 Hoàn thành daily! (+{player['daily_reward']} affection)"

    save_tf_data()
    await ctx.send(f"{text}\n⚡ Energy +{gain}")


@tf.command()
async def sleep(ctx: commands.Context):
    player = get_player(ctx.author.id)
    if not player:
        await ctx.send("❌ Dùng `!tf start` trước.")
        return

    player["energy"] = 10
    player["mood"] = get_mood_text(player["affection"], player["energy"])
    save_tf_data()

    await ctx.send("🌙 Cả hai kết thúc ngày dài. Năng lượng đã hồi đầy.")


@tf.command()
async def talk(ctx: commands.Context):
    player = get_player(ctx.author.id)
    if not player:
        await ctx.send("❌ Dùng `!tf start` trước.")
        return

    if player["energy"] <= 0:
        await ctx.send("❌ Sylvie quá mệt để nói chuyện.")
        return

    player["energy"] -= 1
    gain = random.randint(1, 5)
    player["affection"] += gain
    player["mood"] = get_mood_text(player["affection"], player["energy"])

    dialogues = [
        f"💬 Sylvie: \"...Hôm nay yên bình hơn mình nghĩ.\" (+{gain} affection)",
        f"💬 Sylvie khẽ nhìn bạn rồi nói: \"Cảm ơn vì đã ở đây.\" (+{gain} affection)",
        f"💬 Sylvie im lặng một lúc rồi mỉm cười rất nhẹ. (+{gain} affection)",
        f"💬 Sylvie: \"Mình đang dần quen với cuộc sống này.\" (+{gain} affection)"
    ]
    text = random.choice(dialogues)

    if player["affection"] >= 10 and player["affection"] < 20:
        text += "\n📖 Event mở khóa: Sylvie bắt đầu chủ động nói chuyện hơn."
    elif player["affection"] >= 20 and player["affection"] < 30:
        text += "\n📖 Event mở khóa: Một buổi trò chuyện dài hơn bình thường."
    elif player["affection"] >= 50:
        text += "\n📖 Event đặc biệt: Mối quan hệ đã trở nên rất gần gũi."

    if not player["daily_done"] and player["daily_target"] == "talk":
        player["daily_done"] = True
        player["affection"] += player["daily_reward"]
        text += f"\n🎁 Hoàn thành daily! (+{player['daily_reward']} affection)"

    save_tf_data()
    await ctx.send(text)


@tf.command()
async def nextday(ctx: commands.Context):
    player = get_player(ctx.author.id)
    if not player:
        await ctx.send("❌ Dùng `!tf start` trước.")
        return

    player["day"] += 1
    player["food"] += random.randint(1, 2)
    player["energy"] = max(player["energy"] - 1, 0)
    player["mood"] = get_mood_text(player["affection"], player["energy"])
    ensure_daily(player)
    save_tf_data()

    event = random.choice([
        "🏠 Một ngày mới bắt đầu trong im lặng.",
        "🌤️ Ánh sáng buổi sáng tràn qua khung cửa sổ.",
        "🍃 Không khí hôm nay có vẻ nhẹ nhàng hơn.",
        "📖 Một chương mới nhỏ bé lại bắt đầu."
    ])

    await ctx.send(
        f"{event}\n"
        f"➡️ Day **{player['day']}**\n"
        f"🍞 Nhặt thêm một ít đồ ăn.\n"
        f"🎁 Daily mới: **{player['daily_target']}**"
    )


@tf.command()
async def reset(ctx: commands.Context):
    user_id = str(ctx.author.id)
    if user_id not in tf_players:
        await ctx.send("❌ Bạn chưa có dữ liệu để reset.")
        return

    tf_players.pop(user_id, None)
    save_tf_data()
    await ctx.send("🗑️ Đã xóa dữ liệu mini game của bạn.")


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


@bot.command()
@commands.has_permissions(administrator=True)
async def download(ctx, label: str, link: str):
    embed = discord.Embed(
        title="📦 Tải file",
        description="Nhấn nút bên dưới để tải",
        color=discord.Color.blue()
    )

    view = discord.ui.View()
    button = discord.ui.Button(
        label=label,
        url=link
    )
    view.add_item(button)

    await ctx.send(embed=embed, view=view)


if not TOKEN:
    raise RuntimeError("Thiếu biến môi trường TOKEN")

bot.run(TOKEN)
