# bot.py
from core.report import create_pdf_report
from core.faiss_db import FAISSDatabase
from core.plagiarism import check_plagiarism_online, calculate_similarity
from core.rewriter import rewrite_text
from core.parser import extract_text
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
from dotenv import load_dotenv
import tempfile
import shutil
import nltk
from nltk.tokenize import sent_tokenize

# Загружаем переменные
load_dotenv()

# Импортируем модули

# Скачиваем данные для токенизации
nltk.download('punkt', quiet=True)

# Загружаем переменные
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_ENGINE_ID = os.getenv("GOOGLE_ENGINE_ID")

# Инициализируем базу FAISS
db = FAISSDatabase()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот-антиплагиат.\n\n"
        "Команды:\n"
        "📄 /plagiarism — проверить на плагиат\n"
        "✍️ /rewrite — повысить уникальность\n\n"
        "Отправь текст или файл (.txt, .docx, .pdf, .jpg и др.)"
    )


async def plagiarism(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 Отправь текст или файл для проверки на плагиат.\n"
        "Я проанализирую и выдам отчёт с источниками."
    )
    context.user_data['mode'] = 'plagiarism'


async def rewrite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔄 Отправь текст или файл для перефразирования."
    )
    context.user_data['mode'] = 'rewrite'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode', 'rewrite')

    # Обработка файла
    if update.message.document or update.message.photo:
        if update.message.photo:
            file = await update.message.photo[-1].get_file()
        else:
            file = await update.message.document.get_file()

        file_path = await file.download_to_drive()
        text = extract_text(file_path)

        # Удаляем временный файл
        try:
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
        except:
            pass
    elif update.message.text:
        text = update.message.text
    else:
        await update.message.reply_text("Пожалуйста, отправь текст или файл.")
        return

    if len(text.strip()) < 20:
        await update.message.reply_text("Текст слишком короткий.")
        return

    sentences = sent_tokenize(text)[:8]

    if mode == 'plagiarism':
        await update.message.reply_text("🔍 Анализирую текст... (10–25 сек)")

        total_web_sim = 0
        web_matches_all = []
        faiss_matches_all = []
        high_risk = 0

        for sent in sentences:
            if len(sent) < 15:
                continue

            # Проверка в Google
            web_candidates = check_plagiarism_online(
                sent, GOOGLE_API_KEY, GOOGLE_ENGINE_ID)
            web_sim, best_link = calculate_similarity(sent, web_candidates)
            total_web_sim += web_sim

            if web_sim > 0.4:
                web_matches_all.append({
                    "text": sent,
                    "link": best_link or "#",
                    "similarity": web_sim
                })

            # Проверка в локальной базе
            local_results = db.search(sent, k=2)
            for res in local_results:
                if res['similarity'] > 0.6:
                    faiss_matches_all.append(res)

            if web_sim > 0.7:
                high_risk += 1

        # Оценка уникальности
        avg_web_sim = total_web_sim / len(sentences) if sentences else 0
        plagiarism_percent = avg_web_sim * 100
        uniqueness = 100 - plagiarism_percent

        # Сохраняем в базу, если уникальный
        saved_name = None
        if uniqueness > 70 and len(text) > 300:
            topic = text[:50].replace(' ', '_').replace(
                '.', '').replace(',', '') + f"_{int(uniqueness)}p.txt"
            db.add_text(text, title=topic)
            saved_name = topic

        # Генерация PDF
        try:
            create_pdf_report(
                "report.pdf",
                original=text,
                rewritten=rewrite_text(text),
                plagiarism_score=plagiarism_percent,
                web_matches=web_matches_all,
                faiss_matches=faiss_matches_all
            )
            with open("report.pdf", "rb") as f:
                await update.message.reply_document(f, filename="Отчёт_антиплагиат.pdf")
        except Exception as e:
            await update.message.reply_text(f"📄 PDF не создан: {e}")

        # Текстовый отчёт
        result = f"📊 *Уникальность*: {uniqueness:.0f}%\n⚠️ *Подозрительных фрагментов*: {high_risk}\n\n"

        if web_matches_all:
            result += "*Найдено в интернете:*\n"
            for i, m in enumerate(web_matches_all[:5], 1):
                short = m['text'][:50] + "..."
                result += f"{i}. `{short}` → [ссылка]({m['link']})\n"
            result += "\n"

        if faiss_matches_all:
            result += "*Найдено в базе:*\n"
            for m in faiss_matches_all[:3]:
                result += f"• `{m['text'][:50]}...` → из *{m['title']}*\n"
            result += "\n"

        if saved_name:
            result += f"✅ Работа сохранена как `{saved_name}`\n"

        await update.message.reply_text(result, parse_mode='Markdown')
        context.user_data['mode'] = None

    elif mode == 'rewrite':
        await update.message.reply_text("🔄 Перефразирую через Llama 3...")
        rewritten = rewrite_text(text)
        await update.message.reply_text(f"✨ Уникальная версия:\n\n{rewritten}")
        context.user_data['mode'] = None

# === Запуск бота ===
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plagiarism", plagiarism))
    app.add_handler(CommandHandler("rewrite", rewrite))
    app.add_handler(MessageHandler(
        filters.TEXT | filters.Document.ALL | filters.PHOTO, handle_message))

    print("✅ Бот запущен. Ожидание сообщений...")
    app.run_polling()
