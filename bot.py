import os
import discord
from discord import app_commands
from discord.ext import commands

# =========================
# إعدادات—غير الأرقام بالـ IDs من سيرفرك
# =========================
TOKEN = os.getenv("DISCORD_TOKEN")  # التوكن يضاف من Replit Secrets
GUILD_ID                = 123456789012345678   # ID السيرفر
CHANNEL_VERIFY_ID       = 111111111111111111   # روم "تفعيل"
CHANNEL_APPLICATIONS_ID = 222222222222222222   # روم "استمارات-التفعيل"
ROLE_UNVERIFIED_ID      = 333333333333333333   # رول "غير مفعل"
ROLE_VERIFIED_ID        = 444444444444444444   # رول "مفعل"
ROLE_VERIFY_TEAM_ID     = 555555555555555555   # رول "GALAXY VERIFICATION TEAM"
ROLE_BLACKLIST_ID       = 666666666666666666   # رول "BLACK LIST"

BANNER_URL = "https://cdn.discordapp.com/attachments/1408466066144890973/1410296250187907142/logo.png?ex=68b0803c&is=68af2ebc&hm=77f01157a3bceb80c1d8fd3323fdb61c1a415716ac239c8825be54387385811f&"

# =========================
# البوت
# =========================
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

APPLICATION_INDEX = {}  # لتخزين بيانات الاستمارات

# =========================
# وظائف مساعدة
# =========================
def has_role(member: discord.Member, role_id: int) -> bool:
    return any(r.id == role_id for r in member.roles)

def only_verify_team(interaction: discord.Interaction) -> bool:
    return interaction.user and isinstance(interaction.user, discord.Member) and has_role(interaction.user, ROLE_VERIFY_TEAM_ID)

# =========================
# لما يدخل عضو جديد → نعطيه رول غير مفعل
# =========================
@bot.event
async def on_member_join(member: discord.Member):
    role_unverified = member.guild.get_role(ROLE_UNVERIFIED_ID)
    if role_unverified:
        try:
            await member.add_roles(role_unverified, reason="عضو جديد - إضافة رول غير مفعل تلقائياً")
            print(f"🎯 تم إعطاء {member} رول غير مفعل تلقائياً.")
        except Exception as e:
            print(f"خطأ عند إعطاء رول غير مفعل: {e}")

# =========================
# View: زر التفعيل
# =========================
class VerificationButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="تفعيل", style=discord.ButtonStyle.primary, custom_id="galaxy_verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        if has_role(member, ROLE_BLACKLIST_ID):
            await interaction.response.send_message("❌ لا يمكنك استخدام زر التفعيل (أنت في BLACK LIST).", ephemeral=True)
            return
        if has_role(member, ROLE_VERIFIED_ID):
            await interaction.response.send_message("✅ أنت مفعّل بالفعل.", ephemeral=True)
            return

        await interaction.response.send_modal(VerificationFormModal())

# =========================
# Modal: استمارة التفعيل
# =========================
class VerificationFormModal(discord.ui.Modal, title="استمارة تفعيل GALAXY RP"):
    q1 = discord.ui.TextInput(label="الاسم في الديسكورد (مع التاق)", placeholder="Example#0001", required=True)
    q2 = discord.ui.TextInput(label="الاسم داخل فايف إم", placeholder="اسمك داخل السيرفر", required=True)
    q3 = discord.ui.TextInput(label="العمر", placeholder="مثال: 18", required=True)
    q4 = discord.ui.TextInput(label="البلد/المنطقة الزمنية", placeholder="مثال: السعودية / GMT+3", required=True)
    q5 = discord.ui.TextInput(label="هل قرأت القوانين وتوافق عليها؟", style=discord.TextStyle.paragraph, required=True)
    q6 = discord.ui.TextInput(label="خبرتك في الرول بلاي", style=discord.TextStyle.paragraph, required=True)
    q7 = discord.ui.TextInput(label="سبب رغبتك بالانضمام لـ GALAXY RP", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        apps_ch = interaction.guild.get_channel(CHANNEL_APPLICATIONS_ID)
        if apps_ch is None:
            await interaction.response.send_message("❌ لم يتم العثور على روم الاستمارات.", ephemeral=True)
            return

        embed = discord.Embed(
            title="طلب تفعيل جديد — GALAXY RP",
            description=f"**المتقدم:** {interaction.user.mention}\n**ID:** `{interaction.user.id}`",
            color=discord.Color.blurple()
        )
        embed.set_image(url=BANNER_URL)
        embed.add_field(name="1) الاسم في الديسكورد", value=self.q1.value, inline=False)
        embed.add_field(name="2) الاسم داخل فايف إم", value=self.q2.value, inline=False)
        embed.add_field(name="3) العمر", value=self.q3.value, inline=False)
        embed.add_field(name="4) البلد/المنطقة", value=self.q4.value, inline=False)
        embed.add_field(name="5) القوانين", value=self.q5.value, inline=False)
        embed.add_field(name="6) الخبرة", value=self.q6.value, inline=False)
        embed.add_field(name="7) سبب الانضمام", value=self.q7.value, inline=False)

        view = ApplicationActionView(interaction.user.id)
        msg = await apps_ch.send(embed=embed, view=view)
        APPLICATION_INDEX[msg.id] = {"user_id": interaction.user.id, "claimed_by": None}

        # إضافة فاصل تحت كل استمارة
        await apps_ch.send("──────────────────────────────")

        await interaction.response.send_message("✅ تم إرسال استمارتك، سيتم مراجعتها قريباً.", ephemeral=True)

# =========================
# View: أزرار الاستمارة (الإدارة)
# =========================
class ApplicationActionView(discord.ui.View):
    def __init__(self, applicant_id: int):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    @discord.ui.button(label="استلام", style=discord.ButtonStyle.secondary, custom_id="claim")
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not only_verify_team(interaction):
            await interaction.response.send_message("❌ هذا الزر للفريق فقط.", ephemeral=True)
            return
        APPLICATION_INDEX[interaction.message.id]["claimed_by"] = interaction.user.id
        await interaction.message.channel.send(f"📌 **تم الاستلام** بواسطة {interaction.user.mention}.")
        await interaction.response.send_message("✅ تم الاستلام.", ephemeral=True)

    @discord.ui.button(label="قبول", style=discord.ButtonStyle.success, custom_id="accept")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not only_verify_team(interaction):
            await interaction.response.send_message("❌ هذا الزر للفريق فقط.", ephemeral=True)
            return

        member = interaction.guild.get_member(self.applicant_id)
        if member:
            unv = interaction.guild.get_role(ROLE_UNVERIFIED_ID)
            ver = interaction.guild.get_role(ROLE_VERIFIED_ID)
            if unv in member.roles:
                await member.remove_roles(unv)
            if ver not in member.roles:
                await member.add_roles(ver)
            try:
                await member.send("✅ مبروك! تم قبولك في التفعيل لخادم غالاكسي 🎉")
            except:
                pass
        await interaction.response.send_message("✅ تم القبول.", ephemeral=True)

    @discord.ui.button(label="رفض", style=discord.ButtonStyle.danger, custom_id="reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not only_verify_team(interaction):
            await interaction.response.send_message("❌ هذا الزر للفريق فقط.", ephemeral=True)
            return

        member = interaction.guild.get_member(self.applicant_id)
        if member:
            try:
                await member.send("❌ عذرا تم رفضك في التفعيل لخادم غالاكسي. نتمنى لك حظاً أوفر المرة القادمة.")
            except:
                pass
        await interaction.response.send_message("❌ تم الرفض.", ephemeral=True)

# =========================
# أمر نشر لوحة التفعيل
# =========================
@tree.command(name="post_verification_panel", description="ينشر لوحة التفعيل")
@app_commands.checks.has_permissions(administrator=True)
async def post_verification_panel(interaction: discord.Interaction):
    ch = interaction.guild.get_channel(CHANNEL_VERIFY_ID)
    if ch:
        embed = discord.Embed(
            title="GALAXY RP VERIFICATION CENTRE",
            description=(
                "مرحبا بك في نظام التفعيل لخادم غالاكسي\n"
                "📖 الرجاء قراءة القوانين أولاً\n"
                "➡️ ثم اضغط زر **التفعيل** بالأسفل واملأ الاستمارة"
            ),
            color=discord.Color.blurple()
        )
        embed.set_image(url=BANNER_URL)
        await ch.send(embed=embed, view=VerificationButtonView())
        await interaction.response.send_message("✅ تم نشر لوحة التفعيل.", ephemeral=True)

# =========================
# تشغيل البوت
# =========================
@bot.event
async def on_ready():
    bot.add_view(VerificationButtonView())
    try:
        await tree.sync(guild=discord.Object(id=GUILD_ID))
    except Exception as e:
        print("Sync error:", e)
    print(f"✅ Logged in as {bot.user}")

if __name__ == "__main__":
    bot.run(TOKEN)
