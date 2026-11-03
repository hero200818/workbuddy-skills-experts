"""排版优化：约束标题/正文长度，组装可直接发布的成品文本。"""


class Formatter:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        content = cfg.get("content", {})
        self.title_max = content.get("title", {}).get("max_len", 28)
        self.max_total = cfg.get("platform", {}).get("max_total_len", 2000)

    def finalize(self, item: dict) -> dict:
        """在生成后做排版收口，返回带 publish_text 的 item。"""
        # 标题：选取不超过上限的最短候选，必要时截断
        best = item.get("best_title", "")
        for t in item.get("titles", []):
            cand = t["title"]
            if len(cand) <= self.title_max:
                best = cand
                break
        if len(best) > self.title_max:
            best = best[: self.title_max - 1] + "…"
        item["best_title"] = best

        body = item.get("body", "").strip()
        body = self._ensure_spacing(body)
        # 话题标签追加到正文末尾
        tag = item.get("hashtag_text", "")
        if tag:
            body = f"{body}\n\n{tag}"
        # 总字数上限保护
        if len(best) + len(body) > self.max_total:
            allowed = self.max_total - len(best) - 10
            body = body[:allowed] + "…"

        item["body"] = body
        item["publish_text"] = f"{best}\n\n{body}"
        return item

    def _ensure_spacing(self, body: str) -> str:
        """清理多余空行，保证段落间单空行。"""
        lines = [ln.strip() for ln in body.split("\n")]
        lines = [ln for ln in lines if ln]
        return "\n".join(lines)
