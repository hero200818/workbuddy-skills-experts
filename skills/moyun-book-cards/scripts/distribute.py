#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
distribute.py —— 多平台一键分发文案生成器（墨韵拆书卡 v1.4.0）

读某一期的 books.json（含完整拆书数据）与卡片图片清单，
为三个平台生成「开箱即贴」的分发文案包，输出到 分发包/<期名>/：

  01_微信视频号图文.md   标题(≤20字)+描述+话题+9图上传顺序
  02_头条微头条.md       口语化短文案+互动钩子+话题+配图建议
  03_小红书笔记.md       emoji标题+种草正文+标签+3:4配图建议
  00_素材清单与发布指引.md  图片清单+各平台发布步骤checklist

说明：真实发布需在各平台客户端完成（上传图片+粘贴文案），本工具把
「选图、配文、标签、顺序」全部准备好，做到"一键复制即发布"。

用法：
  python distribute.py <期目录>            # 如 "os.environ.get("MOYUN_CARD_ROOT", os.path.join(os.getcwd(), "畅销书拆书卡"))/2025 年度盘点"
  python distribute.py <期目录>/books.json # 直接给 books.json 也行
"""
import os, sys, json, shutil


def load_data(target):
    """接受期目录或 books.json 路径，返回 (data, imgs)。"""
    if os.path.isfile(target) and target.endswith(".json"):
        bj = target
        period_dir = os.path.dirname(os.path.abspath(bj))
    else:
        period_dir = os.path.abspath(target)
        bj = os.path.join(period_dir, "books.json")
    if not os.path.isfile(bj):
        print(f"[error] 找不到 {bj}")
        sys.exit(1)
    data = json.load(open(bj, encoding="utf-8"))
    # 收集卡片图（按文件名排序，封面 00 在最前）
    imgs = sorted(
        f for f in os.listdir(period_dir)
        if f.endswith(".jpg") and f[:2].isdigit()
    ) if os.path.isdir(period_dir) else []
    return data, imgs, period_dir


def when_word(kind):
    return {"weekly": "本周", "monthly": "本月", "annual": "这一年"}.get(kind, "本期")


def cadence_word(kind):
    return {"weekly": "每周一更新", "monthly": "每月初更新", "annual": "每年初更新"}.get(kind, "定期更新")


def fmt_books_lines(books, style="wx"):
    """按平台口吻排书单。"""
    lines = []
    for i, b in enumerate(books, 1):
        t, a = b.get("title"), b.get("author")
        rec = (b.get("rec") or "").split("。")[0].strip("。") or (b.get("points") or [""])[0]
        if style == "wx":       # 视频号：克制、书卷气
            lines.append(f"《{t}》——{rec}。")
        elif style == "tt":     # 头条：口语、互动
            lines.append(f"{i}️⃣《{t}》{a}｜{rec}")
        else:                   # 小红书：种草、情绪
            lines.append(f"📖《{t}》｜{rec}")
    return "\n".join(lines)


PLATFORM_KEY = {"01_微信视频号图文.md": "weixin", "02_头条微头条.md": "toutiao", "03_小红书笔记.md": "xhs"}


def rules_block(fname):
    """按端附加「平台规则速览」（v1.8.0 运营专家化）。"""
    try:
        rules = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "platforms.json"), encoding="utf-8"))
        r = rules[PLATFORM_KEY.get(fname, "weixin")]
    except Exception:
        return ""
    h = r["hard_rules"]
    return ("\n## 平台规则速览（v1.8.0 运营专家）\n"
            f"- 黄金发布时间：{' / '.join(r['best_time'])}\n"
            f"- 硬规则：图片≤{h['image_max']}张（{h['image_ratio']}）；{h['desc_limit']}；话题：{h['topic_format']}\n"
            f"- 风格：{r['style']}\n"
            f"- 红线：{'；'.join(r['taboos'])}\n"
            f"- 互动策略：{r['interaction']}\n"
            f"- 数据基准：{r['metrics']['good']}（核心：{r['metrics']['core']}）\n")


def gen_weixin(data, imgs):
    books = data["books"]; kind = data.get("kind", "weekly")
    w = when_word(kind)
    n = len(books)
    t1 = books[0].get("title", "")
    order = " → ".join(imgs) if imgs else "00_封面 → 01…08_书卡"
    return f"""# 微信视频号图文 · 发布文案

> 平台：微信「视频号 → 发图文」。竖版 3:4（1080×1350）正好吃满九宫格。

## 标题（三选一，均 ≤20 字）
1. {w}书单｜{n}本热销拆透
2. {n}本好书，一张卡拆读
3. 别刷了，{w}就该读这几本

## 描述（直接粘贴）
📚 {data.get("issue", w + "书单")}来了！

{w}综合各大平台榜单，挑出{n}本最热的书，一本一张中国古典淡雅风拆书卡：核心亮点×3、作者金句×1、适合谁读×1，滑动{len(imgs) or 9}张图3分钟读完👇

📖 {w}拆解：
{fmt_books_lines(books, "wx")}

✅ 想先读哪本？评论区告诉我。
👉 关注我，{cadence_word(kind)}。

#拆书 #畅销书 #书单推荐 #{t1} #{books[1].get("title", "") if n > 1 else "读书"}

## 图片上传顺序
{order}

> 提示：视频号图文上限 9 张，当前 {len(imgs) or 9} 张，正好。
"""


def gen_toutiao(data, imgs):
    books = data["books"]; kind = data.get("kind", "weekly")
    w = when_word(kind)
    n = len(books)
    t1 = books[0].get("title", "")
    return f"""# 今日头条 · 微头条发布文案

> 平台：今日头条 App → 发布 → 微头条。建议配 3 张或 9 张图（用下方图片清单里的前3张或全部）。

## 正文（直接粘贴，约 400 字）
{w}书单来了！这{n}本书最近被全网买爆，我一张张拆给你看📖

{fmt_books_lines(books, "tt")}

说实话，{n}本里我最有共鸣的是《{t1}》——{books[0].get("quote", "")}

这{n}本你读过几本？评论区报个数👇 想看哪本的完整拆解，也尽管点菜！

#畅销书 #书单推荐 #读书 #{t1} #拆书

## 配图建议
- 首发 3 图：{imgs[0] if imgs else "00_封面"} + {imgs[1] if len(imgs) > 1 else "01_书卡"} + {imgs[2] if len(imgs) > 2 else "02_书卡"}
- 九图流：全部 {len(imgs) or 9} 张按序上传（微头条支持 3/4/9 图宫格）

## 互动钩子（可放评论区自己补一条）
"投个票：《{t1}》和《{books[1].get('title') if n > 1 else ''}》只能带一本上荒岛，你选哪本？"
"""


def gen_xiaohongshu(data, imgs):
    books = data["books"]; kind = data.get("kind", "weekly")
    w = when_word(kind)
    n = len(books)
    t1 = books[0].get("title", "")
    tags = " ".join(["#书单推荐", "#读书博主", "#拆书", "#畅销书", "#阅读打卡",
                     f"#{t1}", "#个人成长", "#好书分享"])
    return f"""# 小红书 · 笔记发布文案

> 平台：小红书 App → 发布笔记。1080×1350（3:4）正是小红书最优竖版比例，9 图直接上传。

## 标题（≤20 字，含 emoji）
🔥{w}书单｜{n}本被全网买爆的好书

## 正文（直接粘贴）
姐妹们！{w}书单整理好了📚
每一本都做成了中国古典淡雅风拆书卡，亮点×3+金句+适读人群，一张卡3分钟读懂一本书✨

{fmt_books_lines(books, "xs")}

💡 私心最推荐《{t1}》：
"{books[0].get("quote", "")}"

先读哪本？评论区蹲一个你们的答案👇
关注我，{cadence_word(kind)}，书单永远提前帮你想好💌

{tags}

## 配图
- 封面图（首图）：{imgs[0] if imgs else "00_封面"}（大标题+书单栏，点击率高）
- 内页：{imgs[1] if len(imgs) > 1 else "01_书卡"} 起按序放书卡
"""


def gen_checklist(data, imgs, period_dir):
    kind = data.get("kind", "weekly")
    lines = [
        f"# 素材清单与发布指引 · {data.get('issue', '')}",
        "",
        f"> 源期目录：`{period_dir}`",
        f"> 本分发包含 3 个平台文案 + 下方图片素材。真实上传/粘贴在各平台客户端完成（约 5 分钟/平台）。",
        "",
        "## 一、图片素材（1080×1350 竖版，通用三平台）",
        "",
    ]
    roles = {"00": "封面（首图/大标题）"}
    for i, f in enumerate(imgs):
        tag = f[:2]
        role = roles.get(tag, f"书卡 · 《{(data['books'][i-1] or {}).get('title','') if 1 <= i <= len(data['books']) else ''}》" if tag != "00" else "封面")
        lines.append(f"- `{f}` —— {role}")
    lines += [
        "",
        "## 二、各平台发布步骤",
        "",
        "### 微信视频号图文",
        "1. 打开微信 → 发现 → 视频号 → 发图文",
        "2. 按 `01_微信视频号图文.md` 里的图片顺序上传 9 张",
        "3. 粘贴标题（≤20字）与描述，话题已带 #",
        "4. 发布 ✅",
        "",
        "### 今日头条（微头条）",
        "1. 打开今日头条 App → 发布 → 微头条",
        "2. 配 3 图或 9 图（见文案内建议）",
        "3. 粘贴正文与话题",
        "4. 发布 ✅",
        "",
        "### 小红书",
        "1. 打开小红书 App → 发布笔记",
        "2. 上传 9 张竖版图（3:4 正合适）",
        "3. 粘贴标题与正文，标签已带 #",
        "4. 发布 ✅",
        "",
        f"> 更新节奏提示：{cadence_word(kind)}。期号「{data.get('issue','')}」。",
    ]
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    target = sys.argv[1]
    data, imgs, period_dir = load_data(target)
    books = data.get("books", [])
    if not books:
        print("[error] books 为空")
        sys.exit(1)

    issue = str(data.get("issue", "未命名期")).strip()
    safe_issue = issue.replace("/", "_").replace("\\", "_")
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "分发包", safe_issue)
    os.makedirs(out_dir, exist_ok=True)

    open(os.path.join(out_dir, "01_微信视频号图文.md"), "w", encoding="utf-8").write(gen_weixin(data, imgs) + rules_block("01_微信视频号图文.md"))
    open(os.path.join(out_dir, "02_头条微头条.md"), "w", encoding="utf-8").write(gen_toutiao(data, imgs) + rules_block("02_头条微头条.md"))
    open(os.path.join(out_dir, "03_小红书笔记.md"), "w", encoding="utf-8").write(gen_xiaohongshu(data, imgs) + rules_block("03_小红书笔记.md"))
    open(os.path.join(out_dir, "00_素材清单与发布指引.md"), "w", encoding="utf-8").write(
        gen_checklist(data, imgs, period_dir))

    print(f"✅ 分发包已生成：{out_dir}")
    for f in sorted(os.listdir(out_dir)):
        print(f"   - {f}")
    print(f"   （源期：{issue} | {len(books)} 本书 | {len(imgs)} 张卡片图）")


if __name__ == "__main__":
    main()
