"""可选 LLM 后端：开启后调用 OpenAI 兼容接口增强正文；失败时回退模板。"""
import os


class LLMBackend:
    def __init__(self, cfg: dict):
        llm = cfg.get("llm", {})
        self.enabled = llm.get("enabled", False)
        self.base_url = llm.get("base_url") or None
        self.api_key = llm.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
        self.model = llm.get("model", "gpt-4o-mini")
        self.temperature = llm.get("temperature", 0.9)
        self.max_tokens = llm.get("max_tokens", 800)
        self.fallback = llm.get("fallback_to_template", True)
        self._client = None

    def _init_client(self):
        if self._client is not None:
            return self._client
        if not self.api_key:
            return None
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            return self._client
        except Exception:
            return None

    def generate(self, prompt: str) -> str | None:
        """返回生成文本；未启用 / 无 key / 调用失败均返回 None（交由模板回退）。"""
        if not self.enabled:
            return None
        client = self._init_client()
        if client is None:
            return None
        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return None

    def build_prompt(self, topic: dict) -> str:
        return (
            f"请你以今日头条微头条风格，写一篇关于「{topic.get('title_hint','')}」的短文。"
            f"受众偏好：{topic.get('category','')}类目、情绪基调「{topic.get('emotion','')}」。\n"
            "要求：开头3秒抓人（钩子），中间讲清一个观点或故事，结尾引导互动（评论/点赞/关注）。"
            "语言口语化、有温度，不使用标题党极限词，控制在300字左右，不要出现表情符号以外的特殊格式。"
        )
