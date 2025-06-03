import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os

load_dotenv()

NEWS_API_KEY = os.getenv('NEWS_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)



# Store articles and index globally (or use per-user dictionary if you want)
news_articles = []
current_index = 0

def format_article(article):
    title = article.get('title', 'No title')
    description = article.get('description', '') or ''
    content = article.get('content', '') or ''
    url = article.get('url', '')

    # Remove description from the start of content if it exists to avoid repetition
    if content.startswith(description):
        summary = content
    else:
        summary = description + '\n\n' + content

    summary_lines = summary.split('\n')
    summary_text = '\n'.join(summary_lines[:10]).strip()

    message = f"*{title}*\n\n{summary_text}\n\n[Read more]({url})"
    return message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi! Use /tech to get the latest technology news one at a time.\nUse /other to get the next news article."
    )

async def tech(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global news_articles, current_index

    url = (
        f'https://newsapi.org/v2/top-headlines?'
        f'category=technology&language=en&pageSize=10&apiKey={NEWS_API_KEY}'
    )

    try:
        response = requests.get(url)
        data = response.json()

        if data.get('status') != 'ok':
            await update.message.reply_text("Sorry, couldn't fetch news right now.")
            return

        news_articles = data.get('articles', [])
        if not news_articles:
            await update.message.reply_text("No tech news found at the moment.")
            return

        current_index = 0
        message = format_article(news_articles[current_index])
        await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)

    except Exception as e:
        logger.error(f"Error fetching tech news: {e}")
        await update.message.reply_text("Error fetching news. Please try again later.")

async def other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global news_articles, current_index

    if not news_articles:
        await update.message.reply_text("No news loaded yet. Use /tech first.")
        return

    current_index += 1
    if current_index >= len(news_articles):
        await update.message.reply_text("No more news available. Use /tech to refresh.")
        current_index = len(news_articles) - 1
        return

    message = format_article(news_articles[current_index])
    await update.message.reply_text(message, parse_mode='Markdown', disable_web_page_preview=True)

def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tech", tech))
    app.add_handler(CommandHandler("other", other))

    app.run_polling()

if __name__ == '__main__':
    main()
