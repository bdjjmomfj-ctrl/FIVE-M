import os
import discord
from discord import app_commands
from discord.ext import commands
import requests

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----- Sync Commands -----
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ----- /info -----
@app_commands.command(name="info", description="يعطي معلومات عامة عن حساب Roblox")
@app_commands.describe(username="اسم المستخدم على Roblox")
async def info(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    try:
        search = requests.get(f"https://users.roblox.com/v1/users/search?username={username}").json()
        if search["data"]:
            user = search["data"][0]
            user_id = user["id"]
            display_name = user["displayName"]

            # عدد الأصدقاء
            friends = requests.get(f"https://friends.roblox.com/v1/users/{user_id}/friends").json()
            num_friends = len(friends.get("data", []))

            # Game Passes
            passes = requests.get(f"https://apis.roblox.com/game-passes/v1/users/{user_id}/owned-game-passes").json()
            num_passes = len(passes.get("data", []))

            # آخر ثلاث ألعاب
            activities = requests.get(f"https://games.roblox.com/v1/users/{user_id}/friends-activity").json()
            last_games = [a.get("universeName", "Unknown") for a in activities.get("data", [])[:3]]
            last_games_str = "\n".join(last_games) if last_games else "لا توجد معلومات"

            embed = discord.Embed(title=f"Roblox Info: {username}", color=0x00FF00)
            embed.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={user_id}&width=420&height=420&format=png")
            embed.add_field(name="User ID", value=user_id)
            embed.add_field(name="Display Name", value=display_name)
            embed.add_field(name="عدد الأصدقاء", value=num_friends)
            embed.add_field(name="عدد Game Passes", value=num_passes)
            embed.add_field(name="آخر ثلاث ألعاب دخلها", value=last_games_str, inline=False)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("❌ لم يتم العثور على المستخدم.")
    except Exception as e:
        await interaction.followup.send(f"❌ حدث خطأ: {e}")

# ----- /status -----
@app_commands.command(name="status", description="يعطي حالة اللاعب حالياً")
@app_commands.describe(username="اسم المستخدم على Roblox")
async def status(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    try:
        search = requests.get(f"https://users.roblox.com/v1/users/search?username={username}").json()
        if search["data"]:
            user = search["data"][0]
            user_id = user["id"]

            presence = requests.get(f"https://presence.roblox.com/v1/presence/users?userIds={user_id}").json()
            state = "Offline"
            last_game = "لا توجد لعبة حالية"
            if presence["userPresences"]:
                presence_info = presence["userPresences"][0]
                user_state = presence_info.get("userPresenceType", 0)
                if user_state == 1:
                    state = "Online"
                last_game = presence_info.get("lastLocation", last_game)

            embed = discord.Embed(title=f"Status: {username}", color=0x00FF00)
            embed.add_field(name="الحالة", value=state)
            embed.add_field(name="آخر لعبة", value=last_game)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("❌ لم يتم العثور على المستخدم.")
    except Exception as e:
        await interaction.followup.send(f"❌ حدث خطأ: {e}")

# ----- /robux -----
@app_commands.command(name="robux", description="يعطي نصائح قانونية للحصول على Robux")
async def robux(interaction: discord.Interaction):
    tips = [
        "✅ اشترك في Roblox Premium للحصول على Robux شهريًا.",
        "✅ بيع ملابس أو أشياء في Avatar Marketplace.",
        "✅ صمم لعبة وبيع Game Passes / Dev Products."
    ]
    embed = discord.Embed(title="💡 نصائح Robux", description="\n".join(tips), color=0x00FF00)
    await interaction.response.send_message(embed=embed)

# ----- تسجيل الأوامر -----
bot.tree.add_command(info)
bot.tree.add_command(status)
bot.tree.add_command(robux)

# ----- تشغيل البوت -----
bot.run(os.getenv("DISCORD_TOKEN"))
