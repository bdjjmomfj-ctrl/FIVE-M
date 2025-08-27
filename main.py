import os
import discord
from discord import app_commands
from discord.ext import commands
import requests
from datetime import datetime

# ---------------------------
# إعدادات البوت
# ---------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BANNER = "https://cdn.discordapp.com/attachments/1409928501598883982/1410237724182577232/images.jpg"

# قائمة الأدمنية
ADMINS = [123456789012345678, 987654321098765432]

# ---------------------------
# ستايل إمبيد
# ---------------------------
def styled_embed(title: str, description: str = "", color=0x2ECC71):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_image(url=BANNER)
    embed.timestamp = datetime.utcnow()
    return embed

# ---------------------------
# Event Ready
# ---------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ---------------------------
# /info
# ---------------------------
@app_commands.command(name="info", description="معلومات حساب Roblox")
async def info(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    try:
        res = requests.post("https://users.roblox.com/v1/usernames/users",
                            json={"usernames": [username]}).json()
        if not res.get("data"):
            return await interaction.followup.send("❌ لم يتم العثور على الحساب.")

        user = res["data"][0]
        user_id = user["id"]

        info = requests.get(f"https://users.roblox.com/v1/users/{user_id}").json()
        friends = requests.get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count").json()
        places = requests.get(f"https://games.roblox.com/v2/users/{user_id}/games?limit=3").json()

        embed = styled_embed(f"ℹ️ معلومات {username}", color=0x3498DB)
        embed.add_field(name="🆔 ID", value=user_id, inline=True)
        embed.add_field(name="📅 تاريخ الإنشاء", value=info["created"][:10], inline=True)
        embed.add_field(name="👥 عدد الأصدقاء", value=friends.get("count", "؟"), inline=True)

        games = [g["name"] for g in places.get("data", [])]
        if games:
            embed.add_field(name="🎮 آخر المابات", value="\n".join(games), inline=False)

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ خطأ: {e}")

# ---------------------------
# /robux
# ---------------------------
@app_commands.command(name="robux", description="نصائح لزيادة الروبوكس")
async def robux(interaction: discord.Interaction):
    embed = styled_embed("💰 نصائح للحصول على Robux", color=0xF1C40F)
    embed.add_field(name="1️⃣", value="بيع منتجات داخل ألعابك (Gamepasses).", inline=False)
    embed.add_field(name="2️⃣", value="اشترك في Premium Roblox واحصل على Robux شهري.", inline=False)
    embed.add_field(name="3️⃣", value="شارك في مسابقات Roblox الرسمية.", inline=False)
    await interaction.response.send_message(embed=embed)

# ---------------------------
# /status
# ---------------------------
@app_commands.command(name="status", description="حالة اللاعب في Roblox")
async def status(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    try:
        res = requests.post("https://users.roblox.com/v1/usernames/users",
                            json={"usernames": [username]}).json()
        if not res.get("data"):
            return await interaction.followup.send("❌ لم يتم العثور على الحساب.")

        user_id = res["data"][0]["id"]
        presence = requests.post("https://presence.roblox.com/v1/presence/users",
                                 json={"userIds": [user_id]}).json()

        state = presence["userPresences"][0]["userPresenceType"]
        status_map = {0: "🟥 أوفلاين", 1: "🟩 أونلاين", 2: "🎮 داخل لعبة"}
        status_text = status_map.get(state, "❓ غير معروف")

        embed = styled_embed(f"📡 حالة {username}", color=0xE67E22)
        embed.add_field(name="الحالة", value=status_text, inline=True)

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ خطأ: {e}")

# ---------------------------
# /group
# ---------------------------
@app_commands.command(name="group", description="القروبات اللي لاعب Roblox فيها")
async def group(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    try:
        res = requests.post("https://users.roblox.com/v1/usernames/users",
                            json={"usernames": [username]}).json()
        if not res.get("data"):
            return await interaction.followup.send("❌ لم يتم العثور على الحساب.")

        user_id = res["data"][0]["id"]
        groups = requests.get(f"https://groups.roblox.com/v2/users/{user_id}/groups/roles").json()
        data = groups.get("data", [])

        if not data:
            return await interaction.followup.send("❌ اللاعب غير موجود في أي قروب.")

        embed = styled_embed(f"👥 قروبات {username}", color=0x9B59B6)
        for g in data[:5]:
            group_name = g["group"]["name"]
            role = g["role"]["name"]
            members = g["group"].get("memberCount", "؟")
            embed.add_field(name=group_name, value=f"🎖️ الرتبة: {role}\n👥 الأعضاء: {members}", inline=False)

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ خطأ: {e}")

# ---------------------------
# /device (Placeholder)
# ---------------------------
@app_commands.command(name="device", description="الجهاز اللي اللاعب داخل منه Roblox (Placeholder)")
async def device(interaction: discord.Interaction, username: str):
    embed = styled_embed(f"💻 جهاز {username}", "🔒 هذه المعلومة تحتاج Roblox Cookie لتعمل فعليًا.", color=0x95A5A6)
    await interaction.response.send_message(embed=embed)

# ---------------------------
# /admins_list
# ---------------------------
@app_commands.command(name="admins_list", description="قائمة الأدمنية الخاصة بالبوت")
async def admins_list(interaction: discord.Interaction):
    embed = styled_embed("🛠️ قائمة الأدمنية", color=0x1ABC9C)
    for admin in ADMINS:
        user = await bot.fetch_user(admin)
        embed.add_field(name=user.name, value=f"🆔 {admin}", inline=False)
    await interaction.response.send_message(embed=embed)

# ---------------------------
# /voice (Placeholder)
# ---------------------------
@app_commands.command(name="voice", description="يتحقق إذا مفعل Voice Chat في Roblox (Placeholder)")
async def voice(interaction: discord.Interaction, username: str):
    embed = styled_embed(f"🎤 فحص صوت {username}", "🔒 يتطلب Roblox Cookie لفحص حالة المايك.", color=0xE91E63)
    await interaction.response.send_message(embed=embed)

# ---------------------------
# /bot_rating
# ---------------------------
@app_commands.command(name="bot_rating", description="قيّم البوت بالنجوم")
async def bot_rating(interaction: discord.Interaction):
    view = discord.ui.View()
    for i in range(1, 6):
        async def callback(inter: discord.Interaction, rating=i):
            await inter.response.send_message(f"⭐ شكراً لتقييمك البوت {rating}/5!", ephemeral=True)
        button = discord.ui.Button(label=f"{i}⭐", style=discord.ButtonStyle.primary)
        button.callback = lambda inter, rating=i: callback(inter, rating)
        view.add_item(button)

    embed = styled_embed("⭐ تقييم البوت", "اختر عدد النجوم لتقييم البوت", color=0xF39C12)
    await interaction.response.send_message(embed=embed, view=view)

# ---------------------------
# تشغيل البوت
# ---------------------------
bot.run(DISCORD_TOKEN)
