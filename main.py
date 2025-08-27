import os
import discord
from discord import app_commands
from discord.ext import commands
import requests
from typing import Optional

# ---------- إعداد intents والبوت ----------
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
# message_content مش لازم للـ slash commands لكن نتركها لو احتجت أوامر prefix لاحقاً
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- مساعدة لعمل طلبات آمنة للـ Roblox ----------
REQUEST_TIMEOUT = 8.0

def safe_get_json(url: str, params: dict = None) -> Optional[dict]:
    """تنادي endpoint وترجع json أو None لو فشل"""
    try:
        r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def get_user_id_by_username(username: str) -> Optional[int]:
    """جرب عدة endpoints للحصول على userId"""
    # 1) تجربة endpoint القديم البسيط
    try:
        url1 = f"https://api.roblox.com/users/get-by-username?username={username}"
        j1 = safe_get_json(url1)
        if j1 and isinstance(j1, dict):
            # الشكل القديم يرجع 'Id' أو 'Id' كحرف كبير
            uid = j1.get("Id") or j1.get("id")
            if uid:
                return int(uid)
    except Exception:
        pass

    # 2) تجربة users.search الحديثة (قد ترجع 'data' )
    try:
        url2 = f"https://users.roblox.com/v1/users/search?username={username}"
        j2 = safe_get_json(url2)
        if j2 and isinstance(j2, dict) and j2.get("data"):
            first = j2["data"][0]
            uid = first.get("id") or first.get("userId") or first.get("Id")
            if uid:
                return int(uid)
    except Exception:
        pass

    # 3) تجربة POST endpoint (users by username) - نستخدم GET fallback إن POST غير متاح
    try:
        url3 = "https://users.roblox.com/v1/usernames/users"
        # هذا endpoint عادة يحتاج POST لكن نتحاشاه إذا غير ممكِن
        return None
    except Exception:
        return None

# ---------- دوال fetch للمعلومات ----------
def fetch_user_profile(user_id: int) -> dict:
    """يرجع dict من users.roblox.com/v1/users/{id} أو {}"""
    url = f"https://users.roblox.com/v1/users/{user_id}"
    j = safe_get_json(url)
    return j or {}

def fetch_friends_count(user_id: int) -> int:
    url = f"https://friends.roblox.com/v1/users/{user_id}/friends"
    j = safe_get_json(url)
    if not j:
        return 0
    # بعض الـ endpoints يرجعون 'count' أو 'data'
    if isinstance(j, dict):
        if "count" in j and isinstance(j["count"], int):
            return j["count"]
        data = j.get("data")
        if isinstance(data, list):
            return len(data)
    return 0

def fetch_gamepasses_count(user_id: int) -> Optional[int]:
    url = f"https://apis.roblox.com/game-passes/v1/users/{user_id}/owned-game-passes"
    j = safe_get_json(url)
    if not j:
        return None
    data = j.get("data")
    if isinstance(data, list):
        return len(data)
    return None

def fetch_last_games(user_id: int, limit: int = 3) -> list:
    """
    محاولة الحصول على نشاط الألعاب. قد تفشل بعض الأنظمة؛ نعطي fallback قائمة فارغة.
    """
    url = f"https://games.roblox.com/v1/users/{user_id}/friends-activity"
    j = safe_get_json(url)
    games = []
    if j and isinstance(j, dict) and j.get("data"):
        for a in j["data"][:limit]:
            name = a.get("universeName") or a.get("placeName") or a.get("name")
            if name:
                games.append(name)
    # لو ما في، نجرب presence lastLocation كآخر محاولة
    if not games:
        pres = safe_get_json(f"https://presence.roblox.com/v1/presence/users?userIds={user_id}")
        if pres and isinstance(pres, dict) and pres.get("userPresences"):
            p = pres["userPresences"][0]
            loc = p.get("lastLocation")
            if loc:
                games.append(loc)
    return games

def fetch_presence(user_id: int) -> dict:
    """
    يرجع dict فيه keys: state ('Online'/'Offline') و last_location (string or None)
    """
    res = {"state": "Offline", "last_location": None}
    j = safe_get_json(f"https://presence.roblox.com/v1/presence/users?userIds={user_id}")
    if not j:
        return res
    upr = j.get("userPresences")
    if isinstance(upr, list) and len(upr) > 0:
        info = upr[0]
        user_state = info.get("userPresenceType", 0)  # 1=InGame?, 0=Offline?
        try:
            state = "Online" if int(user_state) == 1 else "Online" if int(user_state) == 2 else "Offline"
        except Exception:
            state = "Online" if user_state else "Offline"
        res["state"] = state
        res["last_location"] = info.get("lastLocation")
    return res

# ---------- أوامر Slash (احترافية وآمنة) ----------
@bot.event
async def on_ready():
    # تسجيل الأوامر (sync) على السيرفرات المسجلة
    try:
        await bot.tree.sync()
    except Exception:
        # لو فشل الـ global sync نتجاهل بس نطبع
        print("⚠️ sync may have failed or taken time")
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

# /info
@app_commands.command(name="info", description="يعطي معلومات عامة عن حساب Roblox")
@app_commands.describe(username="اسم المستخدم على Roblox")
async def cmd_info(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    try:
        uid = get_user_id_by_username(username)
        if not uid:
            await interaction.followup.send("❌ لم يتم العثور على المستخدم. تأكد من كتابة الاسم بشكل صحيح.")
            return

        profile = fetch_user_profile(uid)
        display_name = profile.get("displayName") or profile.get("display_name") or username
        created = profile.get("created") or profile.get("createdTimestamp") or profile.get("createdDate")
        created_str = created if created else "غير متاح"

        friends_count = fetch_friends_count(uid)
        passes_count = fetch_gamepasses_count(uid)
        last_games = fetch_last_games(uid, limit=3)
        last_games_str = "\n".join(last_games) if last_games else "غير متاح"

        # Embed
        embed = discord.Embed(title=f"معلومات Roblox — {username}", color=0x1abc9c)
        # صورة الرأس (headshot)
        embed.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={uid}&width=420&height=420&format=png")
        embed.add_field(name="User ID", value=str(uid), inline=True)
        embed.add_field(name="Display Name", value=str(display_name), inline=True)
        embed.add_field(name="تاريخ الإنشاء", value=str(created_str), inline=False)
        embed.add_field(name="عدد الأصدقاء", value=str(friends_count), inline=True)
        embed.add_field(name="عدد Game Passes (إن أمكن)", value=str(passes_count) if passes_count is not None else "غير متاح", inline=True)
        embed.add_field(name="آخر 3 ألعاب (إن وُجدت)", value=last_games_str, inline=False)

        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ حدث خطأ غير متوقع: `{e}`")

# /status
@app_commands.command(name="status", description="يعطي حالة اللاعب حاليا (Online/Offline) وآخر لعبة")
@app_commands.describe(username="اسم المستخدم على Roblox")
async def cmd_status(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    try:
        uid = get_user_id_by_username(username)
        if not uid:
            await interaction.followup.send("❌ لم يتم العثور على المستخدم.")
            return

        pres = fetch_presence(uid)
        state = pres.get("state", "Offline")
        last_loc = pres.get("last_location") or "غير متاح"

        embed = discord.Embed(title=f"حالة اللاعب — {username}", color=0x3498db)
        embed.add_field(name="الحالة", value=state, inline=True)
        embed.add_field(name="آخر لعبة / موقع", value=str(last_loc), inline=True)
        # صورة الرأس
        embed.set_thumbnail(url=f"https://www.roblox.com/headshot-thumbnail/image?userId={uid}&width=420&height=420&format=png")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ حدث خطأ غير متوقع: `{e}`")

# /robux
@app_commands.command(name="robux", description="نصائح قانونية للحصول على Robux")
async def cmd_robux(interaction: discord.Interaction):
    tips = [
        "1️⃣ اشترك في Roblox Premium لتحصل على Robux شهريًا.",
        "2️⃣ صمم واطلق ملابس أو اكسسوارات على Avatar Marketplace وبيعها.",
        "3️⃣ أنشئ لعبة وبيع Game Passes أو Dev Products داخل لعبتك."
    ]
    embed = discord.Embed(title="💡 نصائح Robux (شرعية وآمنة)", description="\n".join(tips), color=0xf1c40f)
    await interaction.response.send_message(embed=embed)

# تسجيل الأوامر في الـ tree
bot.tree.add_command(cmd_info)
bot.tree.add_command(cmd_status)
bot.tree.add_command(cmd_robux)

# ---------- تشغيل البوت ----------
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("ERROR: Set DISCORD_TOKEN environment variable.")
    else:
        bot.run(TOKEN)
