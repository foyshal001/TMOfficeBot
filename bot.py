import discord
from discord.ext import commands
import datetime
import random
import os
from flask import Flask
from threading import Thread
from zoneinfo import ZoneInfo

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DHAKA = ZoneInfo("Asia/Dhaka")

checkin_time = {}
break_users = {}
break_count = {}
break_total = {}

# ---------------- GOOD MORNING MESSAGES ----------------

gm_messages = [
    "Good Morning! You have been marked in at {time}. Let's make this day count.",
    "Good Morning! Your day has started at {time}. Hope you have a productive day.",
    "Good Morning! Marked in at {time}. Wishing you focus and success today.",
    "Good Morning! You checked in at {time}. Stay motivated and do your best.",
    "Good Morning! You are marked in at {time}. Let's achieve great things today.",
    "Good Morning! Your workday begins at {time}. Make every moment count.",
    "Good Morning! Checked in at {time}. Stay positive and productive.",
    "Good Morning! Your attendance time is {time}. Let's build a successful day.",
    "Good Morning! You started your day at {time}. Stay focused and hydrated.",
    "Good Morning! Marked present at {time}. Wishing you a powerful day ahead."
]

# ---------------- BREAK MESSAGES ----------------

break_messages = [
    "Take a short break and come back with more energy.",
    "Break noted. See you back soon.", "Enjoy your break and recharge.",
    "Break started. Hope you return refreshed.",
    "Take a moment to relax and come back strong.",
    "Break time noted. See you shortly.",
    "Stepping away for a bit. Come back energized.",
    "Take a breather and return ready.", "Break recorded. Catch you soon.",
    "Short break acknowledged."
]

# ---------------- BACK MESSAGES ----------------

back_messages = [
    "Welcome back.", "Hope you had a good break.",
    "Welcome back. Let's continue the work.", "Glad to see you back.",
    "Hope the break refreshed you.", "Back again. Let's focus.",
    "Welcome back. Time to get productive.",
    "Hope you are back with fresh energy.", "Good to have you back.",
    "Break finished. Let's continue."
]

# ---------------- GOOD NIGHT MESSAGES ----------------

gn_messages = [
    "Appreciate your hard work today.", "Great effort today. Rest well.",
    "Thank you for your contribution today.",
    "Another productive day completed.",
    "Good work today. Have a restful night.", "Well done today.",
    "Your effort today is appreciated.", "Thanks for the dedication today.",
    "Closing the day with appreciation.", "Your work today made a difference."
]

# ---------------- KEEP BOT ALIVE ----------------

app = Flask('')


@app.route('/')
def home():
    return "Bot running"


def run():
    app.run(host='0.0.0.0', port=5000)


def keep_alive():
    t = Thread(target=run)
    t.start()


# ---------------- READY ----------------


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")


# ---------------- MESSAGE LISTENER ----------------


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    user = message.author
    content = message.content.lower()

    now = datetime.datetime.now(DHAKA)

    # ---------- GOOD MORNING ----------

    if content in ["gm", "good morning", "in"]:

        checkin_time[user.id] = now
        break_count[user.id] = 0
        break_total[user.id] = 0

        time_str = now.strftime("%H:%M")

        msg = random.choice(gm_messages).format(time=time_str)

        await message.channel.send(f"{user.mention} {msg}")

# ---------- BREAK START ----------

    if content in ["break", "brb"]:

        break_users[user.id] = now

        if user.id not in break_count:
            break_count[user.id] = 0

        break_count[user.id] += 1

        msg = random.choice(break_messages)

        await message.channel.send(f"{user.mention} {msg}")

# ---------- BREAK END ----------

    if content == "back":

        if user.id in break_users:

            start = break_users[user.id]
            minutes = int((now - start).total_seconds() / 60)

            break_total[user.id] += minutes

            num = break_count[user.id]

            suffix = {1: "st", 2: "nd", 3: "rd"}.get(num, "th")

            msg = random.choice(back_messages)

            await message.channel.send(
                f"{user.mention} {msg} It was your {num}{suffix} break. It took {minutes} minutes."
            )

            del break_users[user.id]

# ---------- GOOD NIGHT ----------

    if content in ["gn", "good night", "out"]:

        if user.id in checkin_time:

            start = checkin_time[user.id]

            total_minutes = int((now - start).total_seconds() / 60)

            hours = total_minutes // 60
            mins = total_minutes % 60

            breaks = break_count.get(user.id, 0)
            breakmins = break_total.get(user.id, 0)

            msg = random.choice(gn_messages)

            await message.channel.send(
                f"{user.mention} {msg} Your active hours was {hours} hour {mins} min. You took {breaks} breaks. Total break time was {breakmins} minutes."
            )

# ---------- TAG CHECK ----------

    if message.mentions:

        for m in message.mentions:

            if m.id in break_users:

                start = break_users[m.id]

                minutes = int((now - start).total_seconds() / 60)

                await message.channel.send(
                    f"{m.mention} is currently on break for {minutes} minutes."
                )

    await bot.process_commands(message)


# ---------------- COMMANDS ----------------


@bot.command()
async def whoisonbreak(ctx):

    if not break_users:
        await ctx.send("No one is currently on break.")
        return

    msg = "People currently on break\n"

    now = datetime.datetime.now(DHAKA)

    for uid, start in break_users.items():

        member = ctx.guild.get_member(uid)

        if member:

            minutes = int((now - start).total_seconds() / 60)

            msg += f"{member.display_name} — {minutes} minutes\n"

    await ctx.send(msg)


@bot.command()
async def presenttime(ctx):

    if not checkin_time:
        await ctx.send("No one has checked in yet.")
        return

    msg = "Today's check-in times\n"

    for uid, time in checkin_time.items():

        member = ctx.guild.get_member(uid)

        if member:

            msg += f"{member.display_name} — {time.strftime('%H:%M')}\n"

    await ctx.send(msg)


@bot.command()
async def breakdetails(ctx):

    msg = "Break details today\n"

    for uid in break_count:

        member = ctx.guild.get_member(uid)

        if member:

            b = break_count.get(uid, 0)
            m = break_total.get(uid, 0)

            msg += f"{member.display_name} — {b} breaks — {m} minutes\n"

    await ctx.send(msg)


# ---------------- START BOT ----------------

keep_alive()
bot.run(TOKEN)
