# rewriter.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GROQ = os.getenv("GROQ_API_KEY")


def rewrite_text(text, max_tokens=1024):
    if not GROQ_API_KEY:
        return "[Ошибка: Не задан GROQ_API_KEY в .env]"

    url = "https://api.groq.com/openai/v1/chat/completions"

    prompt = f"""
    Ты — профессиональный рерайтер. Перефразируй текст так, чтобы он стал уникальным,
    сохранив смысл, стиль и логику. Используй синонимы, меняй структуру предложений.
    Подходит для научной работы. Ответ на русском языке.

    Текст:
    {text}
    """

    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": max_tokens
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            return f"[Ошибка {response.status_code}: {response.json().get('error', {}).get('message', 'Неизвестная ошибка')}]"
    except Exception as e:
        return f"[Ошибка сети: {e}]"
