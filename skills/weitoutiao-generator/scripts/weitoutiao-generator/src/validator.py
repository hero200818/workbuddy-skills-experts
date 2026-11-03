"""合规校验：敏感词拦截 + 平台规则检查 + 极限词自动改写。"""
from dataclasses import dataclass

from .data_loader import load_sensitive_words


@dataclass
class Issue:
    level: str          # SEVERE / WARN / INFO
    category: str      # 违规类别
    detail: str        # 命中内容
    suggestion: str    # 处理建议


# 极限词安全改写映射（仅对几乎总是「绝对化」语义的词做自动改写，避免误伤）
_LIMIT_FIX = {
    "极致": "很",
    "顶级": "优秀",
    "绝无仅有": "少见",
    "国家级": "优质",
    "世界级": "出色",
    "100%": "多数",
    "百分之百": "多数",
    "包治": "有助于",
    "根治": "改善",
    "永久": "长期",
    "包治百病": "有助于缓解",
    "药到病除": "有帮助",
    "永不反弹": "不易反弹",
    "彻底治愈": "改善",
    "神效": "不错的效果",
    "一针见效": "较快见效",
}

# 仅标记、不自动改写的绝对化表述（多为多字短语，降低对正常语境的误伤）
_FLAG_ONLY = {
    "最佳", "第一", "唯一", "完美", "万能", "领导者", "首选", "独家",
}


class Validator:
    def __init__(
        self,
        sensitive: dict | None =  None,
        custom_banned: list | None = None,
        auto_fix: bool = True,
    ):
        self.sensitive = sensitive or load_sensitive_words()
        for w in (custom_banned or []):
            self.sensitive[w] = "WARN"
        self.auto_fix = auto_fix

    def check_text(self, text: str) -> tuple[str, list[Issue]]:
        """检查文本中的敏感词，返回 (清洗后文本, 问题列表)。"""
        issues: list[Issue] = []
        clean = text

        if self.auto_fix:
            for word in sorted(_LIMIT_FIX, key=len, reverse=True):
                if word in clean:
                    clean = clean.replace(word, _LIMIT_FIX[word])
                    issues.append(
                        Issue("WARN", "广告法极限词", word,
                              f"已自动改写为「{_LIMIT_FIX[word]}」")
                    )

        skip = set(_LIMIT_FIX.keys()) | _FLAG_ONLY
        for word in sorted(_FLAG_ONLY, key=len, reverse=True):
            if word in clean:
                issues.append(
                    Issue("WARN", "广告法极限词", word,
                          "建议人工复核是否为绝对化表述")
                )

        for word, level in sorted(self.sensitive.items(), key=lambda x: len(x[0]), reverse=True):
            if word in skip:
                continue
            if word in clean:
                if level == "SEVERE":
                    issues.append(
                        Issue("SEVERE", "严重违规", word,
                              "命中严重违规词，建议剔除")
                    )
                else:
                    issues.append(
                        Issue("WARN", "平台/法规风险", word,
                              "建议删除或替换")
                    )

        return clean, issues

    def check_item(self, item: dict, cfg: dict) -> list[Issue]:
        """对整条微头条做平台规则校验（含标题敏感词扫描与长度检查）。"""
        issues: list[Issue] = []
        content = cfg.get("content", {})
        title_max = content.get("title", {}).get("max_len", 28)
        body_cfg = content.get("body", {})
        plat = cfg.get("platform", {})
        max_total = plat.get("max_total_len", 2000)

        # 标题：长度 + 敏感词（仅标记，不改写）
        for t in item.get("titles", []):
            title = t.get("title", "")
            if len(title) > title_max:
                issues.append(
                    Issue("WARN", "标题过长", title[:10] + "…",
                          f"标题超过 {title_max} 字，建议精简以利点击")
                )
            for word in sorted(_FLAG_ONLY, key=len, reverse=True):
                if word in title:
                    issues.append(
                        Issue("WARN", "标题绝对化表述", word,
                              "标题含绝对化用词，建议调整为更克制的表达")
                    )
            skip = set(_LIMIT_FIX.keys()) | _FLAG_ONLY
            for word, level in sorted(self.sensitive.items(), key=lambda x: len(x[0]), reverse=True):
                if word in skip:
                    continue
                if word in title:
                    issues.append(
                        Issue("WARN", "标题风险词", word,
                              "标题含平台/法规风险词，建议删除")
                    )

        # 正文长度
        body = item.get("body", "")
        if len(body) < body_cfg.get("min_len", 120):
            issues.append(
                Issue("WARN", "正文偏短", f"当前 {len(body)} 字",
                      f"建议补足到 {body_cfg.get('min_len')} 字以上")
            )
        if len(body) > body_cfg.get("max_len", 600):
            issues.append(
                Issue("WARN", "正文偏长", f"当前 {len(body)} 字",
                      f"建议控制在 {body_cfg.get('max_len')} 字以内，提升完读率")
            )

        # 总字数
        total = len(item.get("best_title", "")) + len(body)
        if total > max_total:
            issues.append(
                Issue("WARN", "超出字数上限", f"合计 {total} 字",
                      f"微头条建议不超过 {max_total} 字")
            )

        if not item.get("cta"):
            issues.append(
                Issue("INFO", "缺少互动引导", "无 CTA",
                      "建议追加点赞/评论/关注引导，提升互动率")
            )
        if not item.get("hashtags"):
            issues.append(
                Issue("INFO", "缺少话题标签", "无 #话题#",
                      "建议补充 2-3 个话题标签，利于推荐分发")
            )
        if not item.get("image_suggestion"):
            issues.append(
                Issue("INFO", "缺配图建议", "无配图",
                      "微头条配 3-6 张图有助于冷启动")
            )

        return issues
