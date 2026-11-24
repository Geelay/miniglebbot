import os
import logging
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
MY_CHAT_ID = int(os.environ["MY_CHAT_ID"])
MANAGER_CHAT_ID = int(os.environ["MANAGER_CHAT_ID"])

bot = Bot(token=BOT_TOKEN)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != MY_CHAT_ID:
        return
    await update.message.reply_text(
        "Привет! Пиши сообщение — я перешлю его руководителю."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != MY_CHAT_ID:
        return
    try:
        if update.message.text:
            await bot.send_message(chat_id=MANAGER_CHAT_ID, text=update.message.text)
        else:
            await update.message.forward(chat_id=MANAGER_CHAT_ID)
        await update.message.reply_text("✅ Отправлено руководителю.")
    except Exception as e:
        logger.exception("Ошибка при отправке")
        await update.message.reply_text(f"❌ Не удалось отправить: {e}")


def main():
    logger.info("Запуск бота в режиме polling...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    application.run_polling()


if __name__ == "__main__":
    main()
