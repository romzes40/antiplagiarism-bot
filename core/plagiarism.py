# core/plagiarism.py
from sentence_transformers import SentenceTransformer, util
import torch
import requests
import os
from dotenv import load_dotenv

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')


def check_plagiarism_online(text, api_key, engine_id, num_results=3):
    """
    Ищет в Google и возвращает: [{'snippet': ..., 'link': ...}]
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': engine_id,
        'q': text,
        'num': num_results
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return [{"snippet": f"Ошибка API: {response.status_code}", "link": None}]

        items = response.json().get('items', [])
        return [
            {"snippet": item.get('snippet', ''), "link": item.get('link')}
            for item in items if item.get('snippet')
        ]
    except Exception as e:
        return [{"snippet": f"Ошибка: {e}", "link": None}]


def calculate_similarity(original, candidates):
    """
    Оценивает схожесть с лучшим совпадением
    """
    if not candidates:
        return 0.0, None  # (схожесть, лучшая ссылка)

    sentences2 = [c['snippet'] for c in candidates if len(c['snippet']) > 10]
    if not sentences2:
        return 0.0, None

    emb1 = model.encode([original], convert_to_tensor=True)
    emb2 = model.encode(sentences2, convert_to_tensor=True)
    cosine_scores = util.cos_sim(emb1, emb2)
    max_idx = torch.argmax(cosine_scores).item()
    max_sim = cosine_scores[0][max_idx].item()

    best_link = candidates[max_idx]['link']  # ссылка на самый похожий источник
    return max_sim, best_link
