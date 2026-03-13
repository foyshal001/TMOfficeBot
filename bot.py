import discord
from discord.ext import commands
import os
from datetime import datetime
import pytz
from flask import Flask
import threading
import random

# ---- Flask Keep-Alive ----
app = Flask('')

@app.route('/')
def home():
    return "Bot running"

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()

# ---- Discord Token ----
TOKEN = os.environ.get("TOKEN")
if TOKEN is None:
    raise ValueError("TOKEN environment variable not found! Set it in Railway.")

# ---- Bot Setup ----
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---- Data Storage (in memory) ----
users_data = {}  # {user_id: {'day_start': datetime, 'breaks': [{'start':..., 'end':...}]}}
breaking_users = {}  # {user_id: break_start_datetime}

# ---- Message templates ----
gm_messages = [
    "Good Morning! You have been marked in at {time}. Let's make this day count.",
    "Good Morning! Have a productive day ahead ({time}).",
    "Hello! Your day starts now ({time}). Stay motivated!",
    "Good morning! Stay hydrated and energized. ({time})",
    "GM! Make every task today count. ({time})",
    "Rise and shine! Your day begins at {time}.",
    "Top of the morning! Let's crush today's goals. ({time})",
    "Good Morning! Remember to take breaks and stay focused ({time}).",
    "Hello! A new day starts now ({time}).",
    "GM! Ready for a productive day? ({time})"
]

break_messages = [
    "Take care! Come back soon.",
    "Enjoy your break! Return refreshed.",
    "Break time noted. See you soon!"
]

back_messages = [
    "Welcome back! Hope you had a good break.",
    "Back in action! Let's continue.",
    "Hope you are back with a fresh mind."
]

goodnight_messages = [
    "Good night! Appreciate your hard work today.",
    "Night! Hope you had a productive day.",
    "Good night! Rest well for tomorrow.",
    "Thanks for your efforts today. Sleep well!",
    "Day ended! Reflect and recharge for tomorrow.",
    "Good night! Great work today.",
    "Sleep tight! Tomorrow is another chance to shine.",
    "Good night! Stay healthy and motivated.",
    "End of day! See you tomorrow.",
    "Night time! Appreciate your dedication today."
]

# ---- Utility Functions ----
def get_dhaka_time():
    tz = pytz.timezone("Asia/Dhaka")
    return datetime.now(tz)

def format_duration(delta):
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return hours, minutes

# ---- Event Handlers ----
@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    now = get_dhaka_time()

    content = message.content.lower()

    # ---- Good Morning / GM / IN ----
    if content in ["good morning", "gm", "in"]:
        users_data[user_id] = {'day_start': now, 'breaks': []}
        reply = random.choice(gm_messages).format(time=now.strftime("%H:%M"))
        await message.channel.send(f"{message.author.mention} {reply}")
        return

    # ---- Break / BRB ----
    if "break" in content or "brb" in content:
        breaking_users[user_id] = now
        reply = random.choice(break_messages)
        await message.channel.send(f"{message.author.mention} {reply}")
        return

    # ---- Back ----
    if "back" in content:
        if user_id in breaking_users:
            start = breaking_users.pop(user_id)
            delta = now - start
            users_data.setdefault(user_id, {'day_start': now, 'breaks': []})
            users_data[user_id]['breaks'].append({'start': start, 'end': now})
            num_breaks = len(users_data[user_id]['breaks'])
            hours, minutes = format_duration(delta)
            reply = random.choice(back_messages)
            await message.channel.send(
                f"{message.author.mention} {reply} It was your {num_breaks} break and it took {minutes} min."
            )
        return

    # ---- Good Night ----
    if content in ["good night", "gn", "out"]:
        if user_id in users_data:
            day_start = users_data[user_id]['day_start']
            breaks = users_data[user_id]['breaks']
            total_break_seconds = sum([(b['end']-b['start']).seconds for b in breaks])
            total_breaks = len(breaks)
            active_seconds = (now - day_start).seconds - total_break_seconds
            active_hours = active_seconds // 3600
            active_minutes = (active_seconds % 3600) // 60
            reply = random.choice(goodnight_messages)
            await message.channel.send(
                f"{message.author.mention} {reply} Your active hours: {active_hours}h {active_minutes}m. "
                f"You took {total_breaks} breaks. Total break time: {total_break_seconds//60} min."
            )
            # reset user for next day
            users_data.pop(user_id)
        return

    # ---- Tag someone who is on break ----
    for user in message.mentions:
        if user.id in breaking_users:
            delta = get_dhaka_time() - breaking_users[user.id]
            minutes = delta.seconds // 60
            await message.channel.send(
                f"{user.mention} is currently on break for {minutes} min. They will be back soon!"
            )

    # ---- Commands ----
    if content.startswith("!whoisonbreak"):
        if breaking_users:
            msg = "\n".join([f"{bot.get_user(uid).mention} is on break" for uid in breaking_users])
        else:
            msg = "No one is on break currently."
        await message.channel.send(msg)
        return

    if content.startswith("!presenttime"):
        if users_data:
            msg = "\n".join([f"{bot.get_user(uid).mention} came in at {users_data[uid]['day_start'].strftime('%H:%M')}" for uid in users_data])
        else:
            msg = "No one has marked in yet."
        await message.channel.send(msg)
        return

    if content.startswith("!breakdetails"):
        if users_data:
            msg_lines = []
            for uid, data in users_data.items():
                num_breaks = len(data['breaks'])
                total_break_seconds = sum([(b['end']-b['start']).seconds for b in data['breaks']])
                msg_lines.append(f"{bot.get_user(uid).mention}: {num_breaks} breaks, total {total_break_seconds//60} min")
            msg = "\n".join(msg_lines)
        else:
            msg = "No break data available."
        await message.channel.send(msg)
        return

    await bot.process_commands(message)

# ---- Run Bot ----
keep_alive()
bot.run(TOKEN)
