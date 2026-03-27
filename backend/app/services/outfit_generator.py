from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from app.services.ai_stylist_assistant import generate_outfit_explanation


@dataclass
class CatalogItem:
    id: int
    name: str
    category: str  # top, bottom, shoes, accessory
    styles: Set[str]
    colors: Set[str]
    scenarios: Set[str]
    sizes: Set[str]


class OutfitGenerator:
    """Rule-based outfit generator for hackathon MVP.

    Supports style mixing (e.g. casual + sport), color preference and
    basic category composition to return a harmonious outfit.
    """

    NEUTRAL_COLORS = {"black", "white", "gray", "beige"}

    STYLE_KEYWORDS = {
        "sport": ["sport", "jogger", "running", "gym", "sneaker", "athletic"],
        "casual": ["casual", "basic", "denim", "hoodie", "daily", "oversized"],
        "office": ["office", "classic", "formal", "shirt", "trousers", "blazer"],
    }

    def _infer_styles(self, name: str, description: str, style_tags: List[str]) -> Set[str]:
        if style_tags:
            return {s.lower() for s in style_tags}
        text = f"{name} {description}".lower()
        styles: Set[str] = set()
        for style, keys in self.STYLE_KEYWORDS.items():
            if any(k in text for k in keys):
                styles.add(style)
        return styles or {"casual"}

    def _normalize_category_slot(self, category_slug: str) -> str:
        slug = (category_slug or "").lower()
        if "shoe" in slug or "sneaker" in slug:
            return "shoes"
        if "access" in slug or "bag" in slug or "watch" in slug:
            return "accessory"
        if "bottom" in slug or "pant" in slug or "jean" in slug or "trouser" in slug:
            return "bottom"
        return "top"

    def build_catalog(self, products: List[dict], categories_map: Dict[int, str]) -> List[CatalogItem]:
        catalog: List[CatalogItem] = []
        for p in products:
            if not p.get("stock", True):
                continue
            category_slug = categories_map.get(p.get("category_id"), "other")
            slot = self._normalize_category_slot(category_slug)
            name = p.get("name", "")
            description = p.get("description", "") or ""
            style_tags = p.get("style_tags", []) or []
            scenarios = {s.lower() for s in (p.get("scenarios", []) or ["daily"])}
            colors = {c.lower() for c in (p.get("colors", []) or [])}
            sizes = {str(s).upper() for s in (p.get("sizes", []) or [])}

            catalog.append(
                CatalogItem(
                    id=p["id"],
                    name=name,
                    category=slot,
                    styles=self._infer_styles(name, description, style_tags),
                    colors=colors,
                    scenarios=scenarios,
                    sizes=sizes,
                )
            )
        return catalog

    def _normalize_styles(self, style: Optional[str]) -> Set[str]:
        if not style:
            return {"casual"}

        raw = style.lower().replace("+", ",").replace("/", ",").replace(";", ",")
        parts = {p.strip() for p in raw.split(",") if p.strip()}

        # support common aliases
        mapped: Set[str] = set()
        alias = {
            "sporty": "sport",
            "sports": "sport",
            "street": "casual",
        }
        for p in parts:
            mapped.add(alias.get(p, p))

        # ensure we always have a fallback style
        return mapped or {"casual"}

    def _score_item(
        self,
        item: CatalogItem,
        desired_styles: Set[str],
        desired_colors: Set[str],
        scenario: Optional[str],
        desired_sizes: Set[str],
    ) -> float:
        score = 0.0

        style_match = len(item.styles.intersection(desired_styles))
        score += style_match * 2.0

        if scenario and scenario in item.scenarios:
            score += 1.0

        if desired_colors:
            common = len(item.colors.intersection(desired_colors))
            score += common * 1.5

        if desired_sizes and item.sizes and item.sizes.intersection(desired_sizes):
            score += 1.0

        # reward neutral colors for better combinability
        if item.colors.intersection(self.NEUTRAL_COLORS):
            score += 0.5

        return score

    def _compatible_colors(self, a: CatalogItem, b: CatalogItem) -> bool:
        # simple harmony rule: exact match OR one has neutral colors
        same = len(a.colors.intersection(b.colors)) > 0
        neutral = bool(a.colors.intersection(self.NEUTRAL_COLORS) or b.colors.intersection(self.NEUTRAL_COLORS))
        return same or neutral

    def _pick_best(self, candidates: List[tuple[CatalogItem, float]], used_ids: Set[int]) -> Optional[CatalogItem]:
        for item, _ in sorted(candidates, key=lambda x: x[1], reverse=True):
            if item.id not in used_ids:
                return item
        return None

    def generate(
        self,
        products: List[dict],
        categories_map: Dict[int, str],
        style: Optional[str] = None,
        scenario: Optional[str] = None,
        sizes: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Generate one outfit with key categories.

        `sizes` parameter kept for API compatibility; size filtering can be
        connected once products in DB have size inventory.
        """
        desired_styles = self._normalize_styles(style)
        desired_colors = {c.lower() for c in (colors or [])}
        desired_sizes = {str(s).upper() for s in (sizes or [])}
        catalog = self.build_catalog(products, categories_map)

        scored_by_category: Dict[str, List[tuple[CatalogItem, float]]] = {
            "top": [],
            "bottom": [],
            "shoes": [],
            "accessory": [],
        }

        for item in catalog:
            score = self._score_item(item, desired_styles, desired_colors, scenario, desired_sizes)
            if item.category in scored_by_category:
                scored_by_category[item.category].append((item, score))

        used: Set[int] = set()
        result: List[CatalogItem] = []

        top = self._pick_best(scored_by_category["top"], used)
        if top:
            result.append(top)
            used.add(top.id)

        # bottom should be color-compatible with top when possible
        bottoms_sorted = sorted(scored_by_category["bottom"], key=lambda x: x[1], reverse=True)
        bottom = None
        for b, _ in bottoms_sorted:
            if b.id in used:
                continue
            if not top or self._compatible_colors(top, b):
                bottom = b
                break
        if bottom:
            result.append(bottom)
            used.add(bottom.id)

        shoes = self._pick_best(scored_by_category["shoes"], used)
        if shoes:
            result.append(shoes)
            used.add(shoes.id)

        accessory = self._pick_best(scored_by_category["accessory"], used)
        if accessory:
            result.append(accessory)
            used.add(accessory.id)

        return [
            {
                "product_id": item.id,
                "name": item.name,
                "category": item.category,
            }
            for item in result
        ]

    async def generate_with_ai(
        self,
        products: List[dict],
        categories_map: Dict[int, str],
        style: Optional[str] = None,
        scenario: Optional[str] = None,
        sizes: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
    ) -> Dict:
        selected = self.generate(
            products=products,
            categories_map=categories_map,
            style=style,
            scenario=scenario,
            sizes=sizes,
            colors=colors,
        )

        product_map = {p.get("id"): p for p in products}
        outfit = {"top": None, "bottom": None, "shoes": None, "accessory": None}
        total_price = 0.0

        for item in selected:
            slot = item["category"]
            if slot not in outfit or outfit[slot] is not None:
                continue
            source = product_map.get(item["product_id"], {})
            price = float(source.get("price") or 0)
            row = {
                "id": item["product_id"],
                "name": item["name"],
                "price": price,
            }
            outfit[slot] = row
            total_price += price

        selected_items = {k: v for k, v in outfit.items() if v is not None}

        ai_explanation = await generate_outfit_explanation(
            style=style or "casual",
            scenario=scenario or "daily",
            preferred_colors=colors or [],
            selected_items=selected_items,
            catalog=products,
        )

        return {
            "outfit": outfit,
            "ai_explanation": ai_explanation,
            "total_price": round(total_price, 2),
        }
