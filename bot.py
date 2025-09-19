import os
import json
import discord
from discord.ext import commands
from discord import app_commands
import io
import datetime
import asyncio

CONFIG_FILE = "config.json"

# ---------------- JSON CONFIG ----------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

config = load_config()

def get_guild_config(guild_id):
    if str(guild_id) not in config:
        config[str(guild_id)] = {
            "channels": [],
            "exempt_roles": [],
            "exempt_texts": [],
            "paused_until": None
        }
    return config[str(guild_id)]
# ---------------------------------------------

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

# Bot
bot = commands.Bot(command_prefix="!", intents=intents)

async def send_log(guild, embed, file=None):
    guild_conf = get_guild_config(guild.id)
    if guild_conf.get("paused_until"):
        if datetime.datetime.utcnow().timestamp() < guild_conf["paused_until"]:
            return
        else:
            guild_conf["paused_until"] = None
            save_config()
    for chan_id in guild_conf["channels"]:
        channel = guild.get_channel(chan_id)
        if channel:
            await channel.send(embed=embed, file=file)

# ---------------- EVENTS ----------------
@bot.event
async def on_message_delete(message):
    if not message.guild or message.author.bot:
        return
    conf = get_guild_config(message.guild.id)

    if any(role.id in conf["exempt_roles"] for role in message.author.roles):
        return

    if message.content and message.content in conf.get("exempt_texts", []):
        return

    deleter = "Author (self-deleted)"
    try:
        await asyncio.sleep(1)
        async for entry in message.guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
            if (
                entry.target.id == message.author.id
                and (datetime.datetime.now(datetime.timezone.utc) - entry.created_at).total_seconds() < 15
            ):
                deleter = entry.user.mention
                break
    except discord.Forbidden:
        deleter = "Unknown"

    embed = discord.Embed(title="🗑 Message Deleted", color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
    embed.add_field(name="Author", value=message.author.mention, inline=True)
    embed.add_field(name="Deleted By", value=deleter, inline=True)
    embed.add_field(name="Channel", value=message.channel.mention, inline=False)

    if message.content:
        if len(message.content) <= 1024:
            embed.add_field(name="Content", value=message.content, inline=False)
        else:
            embed.add_field(name="Content", value="Too long, see attached file.", inline=False)
            log_buffer = io.StringIO(message.content)
            log_buffer.seek(0)
            file = discord.File(fp=log_buffer, filename=f"deleted_message_{message.id}.txt")
            await send_log(message.guild, embed, file=file)
            return

    if message.attachments:
        embed.add_field(name="Attachments", value="\n".join([a.url for a in message.attachments]), inline=False)

    await send_log(message.guild, embed)

@bot.event
async def on_message_edit(before, after):
    if not after.guild or before.author.bot:
        return
    if before.content == after.content and before.attachments == after.attachments:
        return
    conf = get_guild_config(after.guild.id)
    if any(role.id in conf["exempt_roles"] for role in before.author.roles):
        return

    embed = discord.Embed(title="✏️ Message Edited", color=discord.Color.orange(), timestamp=datetime.datetime.utcnow())
    embed.add_field(name="Author", value=before.author.mention, inline=True)
    embed.add_field(name="Channel", value=before.channel.mention, inline=False)
    if before.content:
        embed.add_field(name="Before", value=before.content, inline=False)
    if after.content:
        embed.add_field(name="After", value=after.content, inline=False)
    await send_log(after.guild, embed)

@bot.event
async def on_bulk_message_delete(messages):
    if not messages:
        return
    guild = messages[0].guild
    if not guild:
        return
    conf = get_guild_config(guild.id)
    count = len(messages)

    moderator = "Unknown"
    try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.message_bulk_delete):
            if (datetime.datetime.now(datetime.timezone.utc) - entry.created_at).total_seconds() < 5:
                moderator = entry.user.mention
    except discord.Forbidden:
        moderator = "Unknown"

    log_buffer = io.StringIO()
    for msg in messages:
        timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        log_buffer.write(f"[{timestamp}] {msg.author} ({msg.author.id}): {msg.content}\n")
    log_buffer.seek(0)
    discord_file = discord.File(
        fp=log_buffer, filename=f"bulk_delete_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
    )

    embed = discord.Embed(title="🧹 Bulk Message Delete", color=discord.Color.dark_red(), timestamp=datetime.datetime.utcnow())
    embed.add_field(name="Moderator", value=moderator, inline=True)
    embed.add_field(name="Channel", value=messages[0].channel.mention, inline=True)
    embed.add_field(name="Messages Deleted", value=str(count), inline=False)
    await send_log(guild, embed, file=discord_file)
# ---------------------------------------------

# ---------------- SLASH COMMANDS ----------------
@bot.tree.command(name="setup", description="Configure the logger bot")
@app_commands.describe(channel="Channel to log to")
async def setup(interaction: discord.Interaction, channel: discord.TextChannel):
    conf = get_guild_config(interaction.guild.id)
    if channel.id not in conf["channels"]:
        conf["channels"].append(channel.id)
        save_config()
        await interaction.response.send_message(f"✅ Added {channel.mention} as a log channel.", delete_after=2)
    else:
        await interaction.response.send_message(f"⚠️ {channel.mention} is already a log channel.", delete_after=2)

@bot.tree.command(name="pause", description="Pause logging for a set duration (in minutes)")
async def pause(interaction: discord.Interaction, minutes: int):
    conf = get_guild_config(interaction.guild.id)
    conf["paused_until"] = datetime.datetime.utcnow().timestamp() + (minutes * 60)
    save_config()
    await interaction.response.send_message(f"⏸️ Logging paused for {minutes} minutes.", delete_after=2)

@bot.tree.command(name="unpause", description="Unpause logging immediately")
async def unpause(interaction: discord.Interaction):
    conf = get_guild_config(interaction.guild.id)
    conf["paused_until"] = None
    save_config()
    await interaction.response.send_message("▶️ Logging unpaused.", delete_after=2)

@bot.tree.command(name="exempt", description="Add an exempt text")
async def exempt(interaction: discord.Interaction, text: str):
    conf = get_guild_config(interaction.guild.id)
    if text not in conf["exempt_texts"]:
        conf["exempt_texts"].append(text)
        save_config()
        await interaction.response.send_message(f"✅ Added `{text}` as exempt text.", delete_after=2)
    else:
        await interaction.response.send_message(f"⚠️ `{text}` is already exempt.", delete_after=2)

@bot.tree.command(name="removeexempt", description="Remove an exempt text")
async def removeexempt(interaction: discord.Interaction, text: str):
    conf = get_guild_config(interaction.guild.id)
    if text in conf["exempt_texts"]:
        conf["exempt_texts"].remove(text)
        save_config()
        await interaction.response.send_message(f"✅ Removed `{text}` from exempt texts.", delete_after=2)
    else:
        await interaction.response.send_message("⚠️ That text was not exempt.", delete_after=2)

@bot.tree.command(name="exemptrole", description="Add a role whose messages won’t be logged")
async def exemptrole(interaction: discord.Interaction, role: discord.Role):
    conf = get_guild_config(interaction.guild.id)
    if role.id not in conf["exempt_roles"]:
        conf["exempt_roles"].append(role.id)
        save_config()
        await interaction.response.send_message(f"✅ Added {role.mention} as an exempt role.", delete_after=2)
    else:
        await interaction.response.send_message(f"⚠️ {role.mention} is already exempt.", delete_after=2)

@bot.tree.command(name="reset", description="Reset all config")
async def reset(interaction: discord.Interaction):
    config[str(interaction.guild.id)] = {"channels": [], "exempt_roles": [], "exempt_texts": [], "paused_until": None}
    save_config()
    await interaction.response.send_message("🔄 Reset complete. Please run /setup again.", delete_after=2)

@bot.tree.command(name="status", description="Show current config")
async def status(interaction: discord.Interaction):
    conf = get_guild_config(interaction.guild.id)
    channels = [f"<#{c}>" for c in conf["channels"]]
    roles = [f"<@&{r}>" for r in conf["exempt_roles"]]
    texts = [f"`{t}`" for t in conf["exempt_texts"]]
    embed = discord.Embed(title="⚙️ Logger Status", color=discord.Color.blue())
    embed.add_field(name="Log Channels", value=", ".join(channels) or "None", inline=False)
    embed.add_field(name="Exempt Roles", value=", ".join(roles) or "None", inline=False)
    embed.add_field(name="Exempt Texts", value=", ".join(texts) or "None", inline=False)
    if conf.get("paused_until"):
        remaining = int(conf["paused_until"] - datetime.datetime.utcnow().timestamp())
        if remaining > 0:
            embed.add_field(name="Paused", value=f"{remaining // 60}m {remaining % 60}s remaining", inline=False)
    await interaction.response.send_message(embed=embed, delete_after=5)

@bot.tree.command(name="testlog", description="Send a test log message")
async def testlog(interaction: discord.Interaction):
    embed = discord.Embed(title="🧪 Test Log", description="This is a test log entry.", color=discord.Color.green())
    await send_log(interaction.guild, embed)
    await interaction.response.send_message("✅ Test log sent.", delete_after=2)

@bot.tree.command(name="help", description="List all bot commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📜 Logger Bot Commands",
        description="Here’s a list of all available commands:",
        color=discord.Color.blue(),
    )
    commands_list = [
        ("/setup <channel>", "Configure the log channel."),
        ("/pause <minutes>", "Pause logging for a set number of minutes."),
        ("/unpause", "Unpause logging immediately."),
        ("/exempt <text>", "Add an exempt text that won’t be logged when deleted."),
        ("/removeexempt <text>", "Remove an exempt text."),
        ("/exemptrole <role>", "Add a role whose messages won’t be logged when deleted/edited."),
        ("/reset", "Reset all configuration for this server."),
        ("/status", "Show current log channels, exempt roles, exempt texts, and pause status."),
        ("/testlog", "Send a test log message to log channels."),
        ("/help", "Show this help message."),
    ]
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)
# ---------------------------------------------

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot logged in as {bot.user}")

    # Debug: fetch and print all commands registered with Discord
    cmds = await bot.tree.fetch_commands()
    print("Registered commands:")
    for cmd in cmds:
        print(f"- {cmd.name}: {cmd.description}")

# ---------------- BOT START ----------------
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("⚠️ DISCORD_BOT_TOKEN is not set. Please configure it in your .env file.")
    bot.run(TOKEN)
