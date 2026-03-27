from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from groq import Groq


def _fallback(style: Optional[str], scenario: Optional[str], preferred_colors: Optional[List[str]], selected_items: Dict) -> str:
    s = style or "casual"
    sc = scenario or "daily"
    colors = ", ".join(preferred_colors or []) or "нейтральные"
    names = ", ".join(v.get("name", "item") for v in selected_items.values()) if selected_items else "базовые вещи"
    return (
        f"Образ в стиле {s} для сценария {sc} собран в палитре: {colors}. "
        f"Вещи ({names}) сочетаются по силуэту и балансу категорий. "
        "Совет: добавьте 1 акцентный аксессуар и держите обувь в нейтральной гамме."
    )


async def generate_outfit_explanation(
    style: str,
    scenario: str,
    preferred_colors: list,
    selected_items: dict,
    catalog: list,
) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return _fallback(style, scenario, preferred_colors, selected_items)

    try:
        client = Groq(api_key=api_key)

        prompt = f"""Ты профессиональный AI-стилист fashion-маркетплейса.

Пользователь хочет образ:
- Стиль: {style}
- Сценарий: {scenario}
- Любимые цвета: {preferred_colors}

Я подобрал следующие вещи из каталога:
{json.dumps(selected_items, ensure_ascii=False, indent=2)}

Объясни почему эти вещи хорошо сочетаются.
Дай 2-3 совета по стилю.
Ответ на русском, коротко и стильно (макс 150 слов)."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Ты стильный AI-стилист. Отвечай коротко, уверенно и модно.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=300,
            temperature=0.7,
        )

        content = response.choices[0].message.content if response.choices else None
        return content or _fallback(style, scenario, preferred_colors, selected_items)
    except Exception:
        return _fallback(style, scenario, preferred_colors, selected_items)
