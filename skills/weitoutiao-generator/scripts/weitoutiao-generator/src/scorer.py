"""爆款潜力评分：从标题力 / 情绪 / 价值 / 互动 / 篇幅 / 排版 多维度打分。"""


class Scorer:
    # 吸引力权重（标题公式类型）
    APPEAL_WEIGHT = {
        "好奇": 25, "共鸣": 24, "对比": 23, "实用": 23, "反差": 22,
        "故事": 21, "警示": 20, "互动": 20, "身份认同": 19, "清单": 22,
    }
    EMOTION_WEIGHT = {
        "共鸣": 20, "温暖": 18, "焦虑": 17, "警示": 17,
        "实用": 16, "好奇": 16, "": 10,
    }

    def score_item(self, item: dict, cfg: dict) -> dict:
        content = cfg.get("content", {})
        title_max = content.get("title", {}).get("max_len", 28)
        optimal = content.get("body", {}).get("optimal_len", 280)

        # 1) 标题力
        appeal = item.get("titles", [{}])[0].get("appeal", "")
        title_power = self.APPEAL_WEIGHT.get(appeal, 20)
        tl = len(item.get("best_title", ""))
        if tl > title_max:
            title_power -= 8
        if tl < 6:
            title_power -= 6
        title_power = max(0, min(25, title_power))

        # 2) 情绪强度
        emo = item.get("emotion", "")
        emotion = self.EMOTION_WEIGHT.get(emo, 12)

        # 3) 实用价值
        value = 8
        if item.get("body_type") in ("干货", "观点"):
            value += 5
        body = item.get("body", "")
        if any(k in body for k in ("建议", "试试", "比如", "可以", "方法", "技巧")):
            value += 2
        value = min(15, value)

        # 4) 互动引导
        interaction = 0
        if item.get("cta"):
            interaction += 8
        if "？" in body or "?" in body:
            interaction += 4
        if any(k in body for k in ("评论", "点赞", "关注", "收藏")):
            interaction += 3
        interaction = min(15, interaction)

        # 5) 篇幅适宜度
        bl = len(body)
        if optimal > 0:
            ratio = 1 - abs(bl - optimal) / optimal
            length = max(0, min(10, int(ratio * 10)))
        else:
            length = 6

        # 6) 排版
        fmt = 0
        if any(ord(c) > 0x1F000 for c in body):  # 含 emoji
            fmt += 4
        if item.get("hashtags"):
            fmt += 3
        if body.count("\n") >= 3:
            fmt += 3
        fmt = min(10, fmt)

        total = title_power + emotion + value + interaction + length + fmt
        label = self._label(total)
        return {
            "title_power": title_power,
            "emotion": emotion,
            "value": value,
            "interaction": interaction,
            "length": length,
            "format": fmt,
            "total": total,
            "label": label,
        }

    def _label(self, total: int) -> str:
        if total >= 85:
            return "爆款相"
        if total >= 70:
            return "优秀"
        if total >= 55:
            return "良好"
        return "一般"
