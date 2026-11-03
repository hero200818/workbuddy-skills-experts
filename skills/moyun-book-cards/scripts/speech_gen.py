#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
speech_gen.py —— 口播视频脚本生成器（墨韵拆书卡 v1.6.0）

把一期拆书文案自动转成「1 分钟视频号口播稿 + 分镜表」：
  - 开场钩子 8s：本期悬念
  - 每本书 6-7s：书名 + 一句话 + 金句（句式轮换不单调）
  - 结尾 CTA 8s：互动提问 + 关注引导
  - 分镜表：时间轴 | 口播词 | 画面（对应哪张卡片）| 备注
九宫格卡片直接当视频素材，一次生产、图文视频通吃。

用法：
  python speech_gen.py <期目录或books.json>
输出：期目录/口播脚本.md
"""
import os, sys, json

WHEN = {"weekly": "本周", "monthly": "本月", "annual": "今年"}

HOOKS = [
    "别再乱买书了。{when}全网最火的{n}本书，我用{n}张卡给你拆明白。",
    "这{n}本书，{when}被全网买爆了。值不值得读？3 分钟给你说清楚。",
    "如果你最近书荒，这{n}本先码住——{when}热销榜我全部拆完了。",
]
CTAS = [
    "这{n}本你读过几本？评论区报个数。关注我，{when}书单永远提前帮你想好。",
    "想先读哪本？评论区告诉我。关注我，下期拆给你看。",
    "收藏这份书单，慢慢读。关注我，每周拆好书。",
]


def hook_line(i, n, when):
    return HOOKS[i % len(HOOKS)].format(n=n, when=when)


def _short(s, n=26):
    s = s.split("。")[0].strip("。")
    if len(s) <= n:
        return s
    cut = s[:n]
    for p in ("，", "、", "；"):
        i = cut.rfind(p)
        if i >= 12:
            return cut[:i]
    return cut


def book_lines(books, when):
    """每本书一句口播（序号词动态、句式轮换），控制单本 6-7 秒。"""
    out = []
    pats = [
        "《{t}》，{rec}。记住这句话——「{q}」",
        "{lead}《{t}》，{rec}。",
        "《{t}》我得重点说：{rec}。",
        "{lead}《{t}》，{rec}。",
        "{rec}——这是《{t}》。",
    ]
    leads = ["先看", "然后是", "接着这本", "还有", "再看", "压轴的是"]
    for i, b in enumerate(books):
        rec = _short(b.get("rec", ""))
        q = (b.get("quote") or "").rstrip("。")
        pat = pats[i % len(pats)]
        lead = leads[min(i - 1, len(leads) - 1)] if i > 0 else ""
        line = pat.format(t=b["title"], rec=rec, q=q, lead=lead)
        if i == 0 and "「" not in line and q:
            line += f"。记住这句话——「{q}」"
        out.append(line)
    return out


def main():
    target = sys.argv[1]
    d = target if os.path.isdir(target) else os.path.dirname(os.path.abspath(target))
    data = json.load(open(os.path.join(d, "books.json"), encoding="utf-8"))
    books, kind = data["books"], data.get("kind", "weekly")
    n, w = len(books), WHEN.get(kind, "本期")

    hook = hook_line(0, n, w)
    hook = hook.replace("最火的", "热度领先的")  # 广告法友好
    body = book_lines(books, w)
    cta = CTAS[0].format(n=n, when=w)

    # 分镜时间轴（口播约 4 字/秒）
    t = 0.0
    rows = [("00:00", "00:08", hook, "00_封面（大标题）", "语速稍快，抛悬念")]
    t = 8.0
    for i, line in enumerate(body, 1):
        dur = max(5, round(len(line) / 4))
        rows.append((f"{t:05.2f}"[:-3].replace(".", ":"), "", line,
                     f"{i:02d}_{books[i-1].get('file', books[i-1]['title'])}",
                     "金句处停顿 0.5s"))
        t += dur
    cta_dur = 8
    rows.append(("≈{:02d}:{:02d}".format(int(t) // 60, int(t) % 60),
                 f"共 {int(t + cta_dur)}s", cta, "回到 00_封面", "结尾引导关注"))

    L = [f"# 口播脚本 · {data.get('issue','')}", "",
         f"> 时长约 {int(t + cta_dur)} 秒（口播 4 字/秒估算）；配图用本期九宫格卡片，逐张切换。",
         "", "## 一、口播全文", "", hook, ""]
    L += body + ["", cta, "", "## 二、分镜表", "",
                 "| 时间 | 口播词 | 画面 | 备注 |", "| --- | --- | --- | --- |"]
    for a, b, line, img, note in rows:
        L.append(f"| {a}{'→' + b if b else ''} | {line} | {img} | {note} |")
    L += ["", "## 三、拍摄提示", "",
          "- 卡片为竖版 1080×1350，视频用 1080×1920 竖屏，上下留白即可；",
          "- 每张卡片停留 5-7 秒，金句可加 0.3 倍速特写；",
          "- 背景音乐：古风轻音乐（音量 15%），金句处压低。"]
    out = os.path.join(d, "口播脚本.md")
    open(out, "w", encoding="utf-8").write("\n".join(L))
    print(f"✅ 口播脚本已生成：{out}（约 {int(t + cta_dur)} 秒）")
    print("   开场：", hook)
    print("   结尾：", cta)


if __name__ == "__main__":
    main()
