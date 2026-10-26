import asyncio
import aiohttp
import re
import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s")

TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

async def verify_card_remotely(visa: str) -> bool:
    url = 'https://checker.visatk.com/ccn1/alien07.php'
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://checker.visatk.com',
        'referer': 'https://checker.visatk.com/ccn1/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    data = {
        'ajax': '1',
        'do': 'check',
        'cclist': visa.strip()
    }
    
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        try:
            async with session.post(url, headers=headers, data=data, timeout=15) as response:
                if response.status == 200:
                    res_text = await response.text()
                    return 'Live' in res_text
        except Exception as e:
            logging.error(f"Checker API request failed: {e}")
        return False

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🤖 **سیستەمی پشکنینی کارتی پارەدان کارایە**\n\n"
        "فەرموو ژمارەی کارتەکە بنێرە بۆ پشکنینی خێرا.",
        parse_mode="Markdown"
    )

@dp.message()
async def handle_card_check(message: types.Message):
    text = message.text.strip()
    if not re.search(r'\d{13,19}', text):
        return

    processing_msg = await message.reply("⏳ خەریکی پشکنینی کارتەکەم...")
    is_live = await verify_card_remotely(text)

    if is_live:
        await processing_msg.edit_text(
            f"✅ **ئەنجام: لایڤ (Live)**\n"
            f"💳 **کارت:** `{text}`\n"
            f"💡 ئەم کارتە کارایە بۆ کڕین.",
            parse_mode="Markdown"
        )
    else:
        await processing_msg.edit_text(
            f"❌ **ئەنجام: دێد (Dead)**\n"
            f"💳 **کارت:** `{text}`\n"
            f"⚠️ ئەم کارتە کارا نییە.",
            parse_mode="Markdown"
        )

async def handle_health_check(request: web.Request) -> web.Response:
    return web.Response(text="Bot is running smoothly!", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"Health check web server started on port {PORT}")

async def main():
    await start_web_server()
    logging.info("Starting Telegram Bot Polling...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped.")
