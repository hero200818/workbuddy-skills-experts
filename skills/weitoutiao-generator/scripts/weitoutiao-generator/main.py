"""微头条爆款批量生成器 - 命令行入口。

用法示例：
  python main.py                         # 按 config.yaml 默认批量生成
  python main.py --count 20 --category 职场
  python main.py --formats json,csv,md,txt --output-dir output
  python main.py --llm                   # 启用大模型后端（需配置 key）
  python main.py --no-validate           # 跳过校验（仅生成）
"""
import argparse
import sys
from pathlib import Path

from src.data_loader import load_config, load_templates, resolve_output_dir
from src.topics import TopicMiner
from src.generator import Generator
from src.validator import Validator
from src.scorer import Scorer
from src.formatter import Formatter
from src.exporter import Exporter
from src.llm_backend import LLMBackend


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="微头条爆款批量生成器")
    p.add_argument("--config", default=None, help="配置文件路径（默认 config.yaml）")
    p.add_argument("--count", type=int, default=None, help="生成条数")
    p.add_argument("--category", default=None, help="指定类目（覆盖权重）")
    p.add_argument("--formats", default=None, help="导出格式，逗号分隔，如 json,csv,md,txt")
    p.add_argument("--output-dir", default=None, help="导出目录")
    p.add_argument("--seed", type=int, default=None, help="随机种子")
    p.add_argument("--no-validate", action="store_true", help="跳过合规校验")
    p.add_argument("--llm", action="store_true", help="启用大模型后端增强")
    return p.parse_args(argv)


def run(args):
    cfg = load_config(args.config)
    gen_cfg = cfg.get("generation", {})
    content_cfg = cfg.get("content", {})
    val_cfg = cfg.get("validator", {})

    count = args.count or gen_cfg.get("count", 12)
    seed = args.seed if args.seed is not None else gen_cfg.get("seed", None)
    category = args.category
    allow_repeat = gen_cfg.get("allow_repeat_category", False)
    strict = val_cfg.get("strict_mode", True)
    min_score = val_cfg.get("min_score_to_keep", 0)

    print(f"[+] 微头条爆款生成器 v{cfg.get('project', {}).get('version','1.0.0')}")
    print(f"[+] 目标条数：{count}  类目：{category or '按权重抽样'}  种子：{seed}")

    # 1) 选题挖掘
    miner = TopicMiner(seed=seed)
    topics = miner.mine(
        count=count,
        category_weights=gen_cfg.get("category_weights", {}),
        category=category,
        allow_repeat_category=allow_repeat,
    )
    print(f"[+] 已挖掘选题 {len(topics)} 个")

    # 2) 生成（标题 + 正文）
    templates = load_templates()
    generator = Generator(templates=templates, seed=seed)
    llm = LLMBackend(cfg)
    if args.llm:
        llm.enabled = True

    raw_items = []
    for t in topics:
        item = generator.build_item(t, cfg)
        if llm.enabled:
            text = llm.generate(llm.build_prompt(t))
            if text:
                item["body"] = text
        raw_items.append(item)

    # 3) 校验
    validator = Validator(
        custom_banned=val_cfg.get("custom_banned_words", []),
        auto_fix=val_cfg.get("auto_fix_limit_words", True),
    )
    formatter = Formatter(cfg)
    scorer = Scorer()

    kept = []
    dropped = 0
    all_issues = []
    for item in raw_items:
        # 文本级敏感词清洗
        if not args.no_validate:
            clean_body, txt_issues = validator.check_text(item.get("body", ""))
            item["body"] = clean_body
            item_issues = txt_issues + validator.check_item(item, cfg)
        else:
            item_issues = []

        severe = [i for i in item_issues if i.level == "SEVERE"]
        if strict and severe:
            dropped += 1
            continue

        # 排版收口
        item = formatter.finalize(item)
        # 打分
        item["score"] = scorer.score_item(item, cfg)
        item["issues"] = [
            {"level": i.level, "category": i.category, "detail": i.detail,
             "suggestion": i.suggestion}
            for i in item_issues
        ]
        all_issues.extend(item_issues)

        if min_score and item["score"]["total"] < min_score:
            dropped += 1
            continue

        kept.append(item)

    # 4) 导出
    out_dir = resolve_output_dir(cfg)
    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    exporter = Exporter(cfg)
    fmts = args.formats.split(",") if args.formats else cfg.get("export", {}).get("formats", ["json", "csv", "md", "txt"])
    exporter.formats = fmts
    written = exporter.export(kept, out_dir)

    # 5) 汇总
    labels = {}
    for it in kept:
        labels[it["score"]["label"]] = labels.get(it["score"]["label"], 0) + 1
    print(f"[+] 生成完成：保留 {len(kept)} 条，剔除 {dropped} 条")
    print(f"[+] 潜力分布：{labels}")
    warn = sum(1 for i in all_issues if i.level == "WARN")
    info = sum(1 for i in all_issues if i.level == "INFO")
    if not args.no_validate:
        print(f"[+] 校验提示：WARN {warn} 条，INFO {info} 条（详见导出文件 issues 字段）")
    print(f"[+] 已导出：{', '.join(written)}")
    return kept, written


def main(argv=None):
    args = parse_args(argv)
    try:
        run(args)
    except Exception as e:
        print(f"[!] 运行失败：{e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
