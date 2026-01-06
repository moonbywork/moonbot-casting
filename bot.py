import os
import random
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== CONFIG =====
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
WEBHOOK_PATH = "/webhook"
HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")
WEBHOOK_URL = f"https://{HOST}{WEBHOOK_PATH}"

# ===== CAST POOLS =====
male = [
    ("Rafiq", 5), ("Ahamad", 5), ("Tirthankar", 5), ("Sanu", 5),
    ("Rezaul", 3), ("Shihab", 3), ("Himu", 3), ("Sohel", 3),
    ("Morshed", 3), ("Ahsan", 3), ("Shawon", 3),
    ("Rabbi", 1),
]

female = [
    ("Shazia", 5), ("Sraboni", 5),
    ("Sharmin", 3), ("Kashkeya", 3), ("Joyashree", 3),
    ("Labanya", 1),
]

def weighted_pick(pool, count, urgent=False):
    names, weights = [], []
    for name, w in pool:
        if urgent and w == 1:
            w = 0.3
        names.append(name)
        weights.append(w)

    selected = set()
    while len(selected) < count:
        selected.add(random.choices(names, weights=weights, k=1)[0])
    return list(selected)

async def cast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    args = context.args
    urgent = False

    if args and args[0].lower() == "urgent":
        urgent = True
        args = args[1:]

    if not args or "m" not in args[0] or "f" not in args[0]:
        await update.message.reply_text(
            "Usage:\n/cast 2m2f Movie Name\n/cast urgent 3m1f Movie Name"
        )
        return

    mix = args[0].lower()
    movie = " ".join(args[1:]) or "Untitled"

    m = int(mix.split("m")[0])
    f = int(mix.split("m")[1].replace("f", ""))

    picks = weighted_pick(male, m, urgent) + weighted_pick(female, f, urgent)

    msg = f"🎬 Movie: {movie}\n🎙 Cast ({mix.upper()}):\n"
    for p in picks:
        msg += f"- {p}\n"

    await update.message.reply_text(msg)

async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return web.Response(text="OK")

async def main():
    global app
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("cast", cast))

    await app.initialize()
    await app.bot.set_webhook(WEBHOOK_URL)
    await app.start()

    web_app = web.Application()
    web_app.router.add_post(WEBHOOK_PATH, webhook_handler)
    web_app.router.add_get("/", lambda r: web.Response(text="OK"))

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()

    print("Private casting bot running...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
