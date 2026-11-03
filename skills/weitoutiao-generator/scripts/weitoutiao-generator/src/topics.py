"""选题挖掘：基于类目权重抽样 + 角度组合，输出去重后的选题清单。"""
import random
from typing import Iterable

from .data_loader import load_topics


class TopicMiner:
    def __init__(self, topics: list[dict] | None = None, seed: int | None = None):
        self.topics = topics or load_topics()
        self.rng = random.Random(seed)

    def _normalize_weights(self, category_weights: dict) -> dict:
        total = sum(category_weights.values()) or 1.0
        return {k: v / total for k, v in category_weights.items()}

    def mine(
        self,
        count: int,
        category_weights: dict | None = None,
        category: str | None = None,
        allow_repeat_category: bool = False,
        seed_weights: bool = True,
    ) -> list[dict]:
        """挖掘 count 个选题。

        - category: 指定类目（覆盖权重）
        - category_weights: 类目权重字典
        - allow_repeat_category: 是否允许同批次同类目重复
        """
        pool = self.topics
        if category:
            pool = [t for t in pool if t["category"] == category]
            if not pool:
                raise ValueError(f"类目「{category}」在选题库中不存在")

        weights = self._normalize_weights(category_weights or {})
        candidates = []
        used_categories = set()
        attempts = 0
        max_attempts = count * 20 + 50

        while len(candidates) < count and attempts < max_attempts:
            attempts += 1
            topic = self._weighted_pick(pool, weights)
            if topic is None:
                break
            cat = topic["category"]
            # 指定单类目时，pool 已过滤，同类目限制无意义，需放开以取足选题
            if not allow_repeat_category and category is None and cat in used_categories:
                continue
            if topic["id"] in {c["id"] for c in candidates}:
                continue
            candidates.append(self._enrich(topic))
            used_categories.add(cat)

        # 若去重导致数量不足，放宽限制补足（带终止守卫，允许选题复用避免死循环）
        attempts2 = 0
        max2 = count * 30 + 50
        while len(candidates) < count and attempts2 < max2:
            attempts2 += 1
            topic = self._weighted_pick(pool, weights)
            if topic is None:
                break
            candidates.append(self._enrich(topic))

        return candidates

    def _weighted_pick(self, pool: list[dict], weights: dict) -> dict | None:
        if not pool:
            return None
        # 按类目权重给每个选题赋权；未配置权重的类目给基础值
        weighted = []
        for t in pool:
            w = weights.get(t["category"], 0.05)
            weighted.extend([t] * max(1, int(w * 100)))
        return self.rng.choice(weighted) if weighted else self.rng.choice(pool)

    def _enrich(self, topic: dict) -> dict:
        """为选题补充「热点角度」与派生关键词，提升差异化。"""
        kw = topic.get("keywords", [])
        angle_pool = [
            "一个被忽略的细节",
            "普通人最容易踩的坑",
            "其实很多人都想错了",
            "越早明白越好",
            "藏在生活里的答案",
            "值得讲给身边的人",
        ]
        enriched = dict(topic)
        enriched["angle"] = self.rng.choice(angle_pool)
        enriched["extra_keyword"] = self.rng.choice(kw) if kw else ""
        return enriched
