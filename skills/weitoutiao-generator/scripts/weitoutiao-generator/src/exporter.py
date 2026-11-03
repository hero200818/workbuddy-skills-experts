"""批量导出：将生成结果输出为 JSON / CSV / Markdown / TXT。"""
import csv
import json
from pathlib import Path


class Exporter:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.formats = cfg.get("export", {}).get("formats", ["json", "csv", "md", "txt"])
        self.prefix = cfg.get("export", {}).get("filename_prefix", "weitoutiao")
        self.include_score = cfg.get("export", {}).get("include_score", True)
        self.delimiter = cfg.get("export", {}).get("csv_delimiter", ",")

    def export(self, items: list[dict], out_dir: Path) -> list[str]:
        written = []
        if "json" in self.formats:
            written.append(self._to_json(items, out_dir))
        if "csv" in self.formats:
            written.append(self._to_csv(items, out_dir))
        if "md" in self.formats:
            written.append(self._to_md(items, out_dir))
        if "txt" in self.formats:
            written.append(self._to_txt(items, out_dir))
        return written

    def _path(self, out_dir: Path, ext: str) -> Path:
        return out_dir / f"{self.prefix}.{ext}"

    def _to_json(self, items, out_dir):
        p = self._path(out_dir, "json")
        data = {
            "count": len(items),
            "items": items,
        }
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return str(p)

    def _to_csv(self, items, out_dir):
        p = self._path(out_dir, "csv")
        fields = [
            "index", "category", "emotion", "best_title", "body",
            "hashtags", "image_suggestion", "label", "total",
        ]
        with open(p, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, delimiter=self.delimiter)
            w.writeheader()
            for i, it in enumerate(items, 1):
                w.writerow({
                    "index": i,
                    "category": it.get("category", ""),
                    "emotion": it.get("emotion", ""),
                    "best_title": it.get("best_title", ""),
                    "body": it.get("body", ""),
                    "hashtags": " ".join(it.get("hashtags", [])),
                    "image_suggestion": it.get("image_suggestion", ""),
                    "label": it.get("score", {}).get("label", "") if self.include_score else "",
                    "total": it.get("score", {}).get("total", "") if self.include_score else "",
                })
        return str(p)

    def _to_md(self, items, out_dir):
        p = self._path(out_dir, "md")
        lines = ["# 微头条批量生成结果", "", f"共生成 {len(items)} 条", ""]
        for i, it in enumerate(items, 1):
            lines.append(f"## {i}. {it.get('best_title', '')}")
            meta = f"类目：{it.get('category','')} ｜ 情绪：{it.get('emotion','')}"
            if self.include_score and it.get("score"):
                s = it["score"]
                meta += f" ｜ 潜力：{s.get('label','')}({s.get('total',0)})"
            lines.append(meta)
            lines.append("")
            lines.append(it.get("publish_text", ""))
            lines.append("")
            lines.append(f"> 配图建议：{it.get('image_suggestion','')}")
            lines.append("")
            lines.append("---")
            lines.append("")
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return str(p)

    def _to_txt(self, items, out_dir):
        p = self._path(out_dir, "txt")
        blocks = []
        for i, it in enumerate(items, 1):
            block = f"【{i}】{it.get('best_title', '')}\n\n{it.get('publish_text', '')}"
            blocks.append(block)
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n\n================================\n\n".join(blocks))
        return str(p)
