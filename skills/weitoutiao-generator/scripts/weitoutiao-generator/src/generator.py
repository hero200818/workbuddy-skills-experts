"""生成引擎：标题候选 + 正文组合（钩子-展开-金句-互动）。"""
import random
from typing import Any

from .data_loader import load_templates


class Generator:
    def __init__(self, templates: dict | None = None, seed: int | None = None):
        self.tpl = templates or load_templates()
        self.rng = random.Random(seed)
        self.formulas = self.tpl.get("title_formulas", [])
        self.openers = self.tpl.get("openers_generic", [])
        self.connectors = self.tpl.get("connectors", [])
        self.cta_pool = self.tpl.get("cta_pool", [])
        self.emoji_pool = self.tpl.get("emoji_pool", [])
        self.category_emoji = {
            "情感": "❤️", "社会": "🤝", "职场": "💼", "健康": "💪",
            "美食": "🍜", "科技": "📱", "历史": "📜", "财经": "💰",
            "育儿": "👶", "宠物": "🐱",
        }

    # ---------- 标题 ----------
    def gen_titles(self, topic: dict, variants: int = 3) -> list[dict]:
        """为选题生成多个标题候选，附带公式类型与吸引力标签。"""
        topic_text = topic.get("title_hint", "")
        out = []
        seen = set()
        attempts = 0
        while len(out) < variants and attempts < variants * 8:
            attempts += 1
            formula = self.rng.choice(self.formulas)
            title = formula["template"].format(topic=topic_text)
            if title in seen:
                continue
            seen.add(title)
            out.append(
                {
                    "title": title,
                    "formula": formula["name"],
                    "appeal": formula.get("appeal", ""),
                }
            )
        return out

    # ---------- 正文 ----------
    def gen_body(self, topic: dict, emoji_density: float = 1.1) -> dict:
        """组合正文：开头钩子 + 要点展开 + 金句 + 互动引导。"""
        hook = topic.get("hook", self.rng.choice(self.openers))
        points = list(topic.get("points", []))
        self.rng.shuffle(points)
        punchline = topic.get("punchline", "")
        cta = self.rng.choice(self.cta_pool)

        # 用连接词把要点串成段落
        body_parts = [hook]
        for i, p in enumerate(points[:3]):
            if i > 0 and self.rng.random() < 0.6:
                conn = self.rng.choice(self.connectors)
                body_parts.append(f"{conn}{p}")
            else:
                body_parts.append(p)
        body_parts.append(punchline)
        body_parts.append(cta)

        text = "\n".join(body_parts)
        text = self._inject_emoji(text, emoji_density, topic.get("category"))
        return {
            "body": text,
            "hook": hook,
            "punchline": punchline,
            "cta": cta,
        }

    def _inject_emoji(self, text: str, density: float, category: str | None = None) -> str:
        """按密度在段落间插入 emoji，优先使用类目匹配图标，避免重复。"""
        lines = [ln for ln in text.split("\n") if ln.strip()]
        if not lines:
            return text
        n_emoji = max(0, int(len(text) / 100 * density))
        used = set()
        cat_emoji = self.category_emoji.get(category)
        # 优先放置类目 emoji，保证图文气质一致
        if cat_emoji and n_emoji >= 1:
            idx = self.rng.randint(0, len(lines) - 1)
            lines[idx] = f"{cat_emoji} {lines[idx]}"
            used.add(cat_emoji)
            n_emoji -= 1
        pool = list(self.emoji_pool)
        for _ in range(n_emoji):
            idx = self.rng.randint(0, len(lines) - 1)
            emoji = self.rng.choice(pool)
            if emoji in used:
                continue
            used.add(emoji)
            lines[idx] = f"{emoji} {lines[idx]}"
        return "\n".join(lines)

    def build_item(self, topic: dict, cfg: dict) -> dict:
        """组装单条微头条成品（标题候选 + 正文 + 元信息）。"""
        content_cfg = cfg.get("content", {})
        title_cfg = content_cfg.get("title", {})
        hashtags_cfg = content_cfg.get("hashtags", {})

        titles = self.gen_titles(topic, title_cfg.get("variants", 3))
        body_obj = self.gen_body(topic, content_cfg.get("emoji_per_100_chars", 1.1))

        # 话题标签
        hcount = hashtags_cfg.get("count", [2, 3])
        lo, hi = (hcount if isinstance(hcount, list) else [hcount, hcount])
        n_tags = self.rng.randint(int(lo), int(hi))
        tags = topic.get("hashtags", [])[:n_tags]
        style = hashtags_cfg.get("style", "double_hash")
        if style == "double_hash":
            tag_text = " ".join(f"#{t}#" for t in tags)
        else:
            tag_text = " ".join(f"#{t}" for t in tags)

        # 配图建议
        img_sug = self.rng.choice(
            self.tpl.get("image_prompt_pool", ["建议配图 3-6 张"])
        )

        return {
            "topic_id": topic["id"],
            "category": topic["category"],
            "emotion": topic.get("emotion", ""),
            "keywords": topic.get("keywords", []),
            "titles": titles,
            "best_title": titles[0]["title"] if titles else "",
            "body": body_obj["body"],
            "hook": body_obj["hook"],
            "punchline": body_obj["punchline"],
            "cta": body_obj["cta"],
            "hashtags": tags,
            "hashtag_text": tag_text,
            "image_suggestion": img_sug,
            "body_type": topic.get("body_type", ""),
        }
