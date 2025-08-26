import discord
from discord.ext import commands
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    guild = ctx.guild

    # ✅ إنشاء الرولات مع الصلاحيات
    roles = {
        "Server Owner": discord.Permissions(administrator=True),
        "Co Owner": discord.Permissions(administrator=True),
        "Vice Founder": discord.Permissions(manage_guild=True, manage_roles=True, manage_channels=True, kick_members=True, ban_members=True),
        "FIVE M High Management": discord.Permissions(manage_guild=True, manage_channels=True, kick_members=True, ban_members=True, manage_messages=True),
        "FIVE M Management": discord.Permissions(manage_messages=True, mute_members=True, move_members=True),
        "Discord Admin": discord.Permissions(manage_messages=True, kick_members=True),
        "Discord Supporter": discord.Permissions(manage_messages=True),
        "VIP Individuel": discord.Permissions(read_messages=True, send_messages=True),
        "Artist": discord.Permissions(read_messages=True, send_messages=True),
        "Youtuber": discord.Permissions(read_messages=True, send_messages=True, stream=True),
        "Galaxy Verified": discord.Permissions(read_messages=True, send_messages=True),
        "Unactivated": discord.Permissions(read_messages=True)
    }

    for role_name, perms in roles.items():
        existing = discord.utils.get(guild.roles, name=role_name)
        if not existing:
            await guild.create_role(name=role_name, permissions=perms)
    
    # ✅ إنشاء الكاتيجوريات والرومات
    categories = {
        "Base": ["rules", "announcements", "server-info"],
        "General": ["chat", "media", "memes"],
        "Ticket": ["support", "report"],
        "Voice": ["General Voice", "Music", "Lounge"]
    }

    for cat_name, chans in categories.items():
        cat = discord.utils.get(guild.categories, name=cat_name)
        if not cat:
            cat = await guild.create_category(cat_name)
        for ch in chans:
            if not discord.utils.get(guild.channels, name=ch):
                if "voice" in ch.lower() or "music" in ch.lower() or "lounge" in ch.lower():
                    await guild.create_voice_channel(ch, category=cat)
                else:
                    await guild.create_text_channel(ch, category=cat)

    await ctx.send("✅ تم تجهيز السيرفر بكل شيء!")

bot.run(os.getenv("DISCORD_TOKEN"))
