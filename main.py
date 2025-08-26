import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def setup(ctx):
    guild = ctx.guild

    # ========== إنشاء الرولات ==========
    roles = {
        "Server Owner": discord.Permissions(administrator=True),
        "Co Owner": discord.Permissions(manage_guild=True, manage_channels=True, kick_members=True, ban_members=True, view_audit_log=True),
        "Vice Founder": discord.Permissions(manage_channels=True, kick_members=True, ban_members=True, change_nickname=True, view_audit_log=True),
        "FIVE M High Management": discord.Permissions(kick_members=True, ban_members=True, moderate_members=True, move_members=True, view_audit_log=True),
        "FIVE M Management": discord.Permissions(kick_members=True, moderate_members=True, mute_members=True, deafen_members=True, change_nickname=True),
        "Member": discord.Permissions(send_messages=True, connect=True, speak=True, attach_files=True, embed_links=True),
        "Bot": discord.Permissions(administrator=True)
    }

    for role_name, perms in roles.items():
        if not discord.utils.get(guild.roles, name=role_name):
            await guild.create_role(name=role_name, permissions=perms)

    # ========== إنشاء الكاتيجوريات + الرومات ==========
    categories = {
        "📌 Base": ["rules", "announcements", "server-info"],
        "💬 General": ["chat", "server-media", "clips"],
        "🎟️ Ticket": ["support"],
        "🎤 Voice": ["Voice 1", "Voice 2", "Voice 3", "Create Your Voice"]
    }

    for cat_name, channels in categories.items():
        category = discord.utils.get(guild.categories, name=cat_name)
        if category is None:
            category = await guild.create_category(cat_name)
        
        for ch in channels:
            if not discord.utils.get(category.channels, name=ch.lower()):
                if "Voice" in cat_name or "Voice" in ch:
                    await guild.create_voice_channel(ch, category=category)
                else:
                    await guild.create_text_channel(ch, category=category)

    await ctx.send("✅ تم إنشاء الرولات والرومات بنجاح!")

# تشغيل البوت من التوكن الموجود في Secrets
bot.run(os.getenv("DISCORD_TOKEN"))
