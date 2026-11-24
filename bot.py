import os
import logging
from aiohttp import web
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Переменные окружения ---
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
MY_CHAT_ID = int(os.environ["MY_CHAT_ID"])
MANAGER_CHAT_ID = int(os.environ["MANAGER_CHAT_ID"])
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # если задан — режим webhook
WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET")

bot = Bot(token=BOT_TOKEN)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пересылает всё, что вы написали боту в личке, руководителю."""
    if update.effective_chat.id != MY_CHAT_ID:
        return  # игнорируем сообщения из других чатов

    # Берём текст; если сообщение не текстовое (фото/файл) — пересылаем как есть
    text = update.message.text
    try:
        if text:
            await bot.send_message(chat_id=MANAGER_CHAT_ID, text=text)
        else:
            await update.message.forward(chat_id=MANAGER_CHAT_ID)
        await update.message.reply_text("✅ Отправлено руководителю.")
    except Exception as e:
        logger.exception("Ошибка при отправке руководителю")
        await update.message.reply_text(f"❌ Не удалось отправить: {e}")


async def webhook_handler(request):
    """Принимает обновления от Telegram."""
    if WEBHOOK_SECRET:
        if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
            return web.Response(status=403)

    try:
        data = await request.json()
        update = Update.de_json(data, bot)
        app = (
            Application.builder()
            .token(BOT_TOKEN)
            .build()
        )
        app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
        await app.initialize()
        await app.process_update(update)
        await app.shutdown()
        return web.Response(text="ok")
    except Exception as e:
        logger.exception("Ошибка в webhook_handler")
        return web.Response(status=500, text=str(e))


if __name__ == "__main__":
    if WEBHOOK_URL:
        logger.info("Режим webhook. Слушаем 0.0.0.0:%s", os.environ.get("PORT", 8080))
        app = web.Application()
        app.router.add_post("/webhook", webhook_handler)
        web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    else:
        logger.info("WEBHOOK_URL не задан — режим polling (для локальной отладки).")
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(
            MessageHandler(filters.ALL & ~filters.COMMAND, handle_message)
        )
        application.run_polling()
