"""配置与数据加载器：统一管理 config / 选题 / 模板 / 敏感词。"""
import json
import os
from pathlib import Path
from typing import Any

import yaml

# 项目根目录：src 的上一级
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def load_config(path: str | None = None) -> dict:
    """加载 YAML 主配置；缺失时返回内置默认配置。"""
    cfg_path = Path(path) if path else CONFIG_PATH
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    raise FileNotFoundError(f"未找到配置文件：{cfg_path}")


def load_topics(path: str | None = None) -> list[dict]:
    """加载选题种子库。"""
    p = Path(path) if path else DATA_DIR / "topics_seed.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)["topics"]


def load_templates(path: str | None = None) -> dict:
    """加载标题/正文模板库。"""
    p = Path(path) if path else DATA_DIR / "templates.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def load_sensitive_words(path: str | None = None) -> dict[str, str]:
    """加载敏感词库，返回 {词语: 级别} 映射。"""
    p = Path(path) if path else DATA_DIR / "sensitive_words.txt"
    result: dict[str, str] = {}
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "||" in line:
                word, level = line.split("||", 1)
                result[word.strip()] = level.strip()
            else:
                result[line] = "WARN"
    return result


def resolve_output_dir(cfg: dict) -> Path:
    """解析导出目录绝对路径（相对项目根）。"""
    out = cfg.get("export", {}).get("output_dir", "output")
    path = Path(out)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path.mkdir(parents=True, exist_ok=True)
    return path
