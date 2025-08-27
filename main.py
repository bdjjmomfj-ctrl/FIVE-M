import os
import discord
from discord import app_commands
from discord.ext import commands
import requests

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------------
# Function: Get Roblox User ID
# ----------------------------
def get_user_id(username: str):
    url = "https://users.roblox.com/v1/usernames/users"
    body = {"usernames": [username], "excludeBannedUsers": True}
    res = requests.post(url, json=body).json()
    if res.get("data") and len(res["data"]) > 0:
        return res["data"][0]  # يرجع dict فيه id + الاسم
    return None

# ----------------------------
# Event: Bot Ready
# ----------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ----------------------------
# Command: /info
# ----------------------------
@app_commands.command(name="info", description="يعطيك معلومات عن حساب Roblox")
@app_commands.describe(username="اسم المستخدم في Roblox")
async def info(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    user = get_user_id(username)
    if not user:
        return await interaction.followup.send("❌ لم يتم العثور على المستخدم.")

    user_id = user["id"]
    display_name = user["displayName"]

    # الأصدقاء
    friends = requests.get(f"https://friends.roblox.com/v1/users/{user_id}/friends").json()
    num_friends = len(friends.get("data", [])) if friends.get("data") else 0

    # Game Passes
    passes = requests.get(
        f"https://inventory.roblox.com/v1/users/{user_id}/assets/1"
    ).json()
    num_passes = len(passes.get("data", [])) if passes.get("data") else 0

    # Avatar image
    avatar = f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=420&height=420&format=png"

    embed = discord.Embed(title=f"ℹ️ Roblox Info: {username}", color=0x00FF00)
    embed.set_thumbnail(url=avatar)
    embed.add_field(name="User ID", value=user_id)
    embed.add_field(name="Display Name", value=display_name)
    embed.add_field(name="عدد الأصدقاء", value=num_friends)
    embed.add_field(name="عدد Game Passes", value=num_passes)
    await interaction.followup.send(embed=embed)

# ----------------------------
# Command: /status
# ----------------------------
@app_commands.command(name="status", description="يعرض حالة لاعب Roblox (اونلاين/اوفلاين)")
@app_commands.describe(username="اسم المستخدم في Roblox")
async def status(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    user = get_user_id(username)
    if not user:
        return await interaction.followup.send("❌ لم يتم العثور على المستخدم.")

    user_id = user["id"]

    presence = requests.post(
        "https://presence.roblox.com/v1/presence/users",
        json={"userIds": [user_id]}
    ).json()

    state = "Offline"
    last_game = "لا توجد معلومات"
    if presence.get("userPresences"):
        info = presence["userPresences"][0]
        if info.get("userPresenceType") == 1:
            state = "🟢 Online"
        elif info.get("userPresenceType") == 2:
            state = "🟡 In-Game"
        last_game = info.get("lastLocation", last_game)

    embed = discord.Embed(title=f"📊 Status: {username}", color=0x00AAFF)
    embed.add_field(name="الحالة", value=state)
    embed.add_field(name="آخر لعبة", value=last_game, inline=False)
    await interaction.followup.send(embed=embed)

# ----------------------------
# Command: /robux
# ----------------------------
@app_commands.command(name="robux", description="يعطي نصائح قانونية للحصول على Robux")
async def robux(interaction: discord.Interaction):
    tips = [
        "✅ اشترك في Roblox Premium للحصول على Robux شهريًا.",
        "✅ بيع ملابس أو أدوات في Avatar Marketplace.",
        "✅ أنشئ لعبة وبيع Game Passes أو Dev Products."
    ]
    embed = discord.Embed(title="💡 نصائح للحصول على Robux", description="\n".join(tips), color=0xFFD700)
    await interaction.response.send_message(embed=embed)

# ----------------------------
# Add Commands
# ----------------------------
bot.tree.add_command(info)
bot.tree.add_command(status)
bot.tree.add_command(robux)

# ----------------------------
# Run Bot
# ----------------------------
bot.run(os.getenv("DISCORD_TOKEN"))
