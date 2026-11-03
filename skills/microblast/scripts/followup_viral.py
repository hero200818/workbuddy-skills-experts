#!/usr/bin/env python3
"""追爆续集脚本：输入爆款ID，自动识别其结构，生成同结构续集内容
用法：python3 scripts/followup_viral.py <爆款ID> [续集数量]
示例：python3 scripts/followup_viral.py P01_d12_n2 3
"""
import json, sys, os, subprocess, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(BASE, "references")

def load_content(cid):
    """按ID加载内容库条目"""
    # P01_dXX_nN → dayXX_numN.json
    m = re.match(r'P01_d(\d+)_n(\d+)', cid)
    if not m:
        return None
    path = os.path.join(LIB, f"day{int(m.group(1))}_num{m.group(2)}.json")
    if not os.path.exists(path):
        return None
    return json.load(open(path, encoding="utf-8"))

def extract_theme_keyword(theme, content):
    """从主题文本映射到生成器主题关键词"""
    t = (theme or "") + " " + (content or "")
    if any(k in t for k in ["外卖", "吃饭", "骑手", "餐"]): return "takeout"
    if any(k in t for k in ["工资", "收入", "发工资", "余额", "账"]): return "salary"
    if any(k in t for k in ["亲戚", "大姑", "人情", "随礼", "借钱", "关系"]): return "relative"
    if any(k in t for k in ["35", "岁", "中年", "鬓角", "叔叔"]): return "age35"
    if any(k in t for k in ["家", "妈", "爸", "父母", "亲情"]): return "family"
    return "salary"  # 默认工资（best_theme）

def analyze_structure(content):
    """分析爆款结构特征"""
    features = []
    # 数字密度
    nums = re.findall(r'\d+', content)
    if len(nums) >= 3:
        features.append(f"多数字对比({len(nums)}处)")
    # 生理反应
    if any(k in content for k in ["心里", "喉", "心", "脸", "手", "胃", "嘴", "眼"]):
        features.append("含生理反应")
    # 35岁感慨
    if "35" in content:
        features.append("含35岁身份锚点")
    # 结尾提问
    if content.rstrip().endswith(("吗？", "呢？", "吧？", "？")):
        features.append("结尾开放式提问")
    # 冲突开头
    if content.startswith(("今天", "今早", "昨晚", "刚")):
        features.append("第一人称即时场景开头")
    return features

def main():
    if len(sys.argv) < 2:
        print("用法: python3 followup_viral.py <爆款ID> [数量]")
        print("示例: python3 followup_viral.py P01_d12_n2 3")
        sys.exit(1)
    cid = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    rec = load_content(cid)
    if not rec:
        print(f"❌ 未找到内容 {cid}")
        sys.exit(1)

    print(f"📊 分析爆款 {cid}:")
    print(f"   主题: {rec.get('theme')}")
    print(f"   内容: {rec.get('content')[:80]}...")
    feats = analyze_structure(rec.get("content", ""))
    print(f"   爆款结构特征: {', '.join(feats) if feats else '常规'}")

    theme_key = extract_theme_keyword(rec.get("theme"), rec.get("content"))
    print(f"   → 续集主题映射: {theme_key}")
    print(f"\n🚀 生成 {n} 条同结构续集...\n")

    # 记录生成前内容库最大day（用于识别本次新增）
    before_days = [int(f.split('_')[0][3:]) for f in os.listdir(LIB) if f.startswith('day')]
    max_day_before = max(before_days) if before_days else 0

    # 调用生成器 save
    result = subprocess.run(
        ["python3", os.path.join(BASE, "scripts/content_generator.py"), "save", theme_key, str(n)],
        capture_output=True, text=True, cwd=BASE
    )
    print(result.stdout[-1500:])
    if result.returncode != 0:
        print("STDERR:", result.stderr[-500:])
        sys.exit(1)

    # 续集叙事增强：识别本次新增内容，标记续集关联 + 添加"续集开场"视角
    followup_templates = [
        "上次那件事，今天有了后续。",
        "接着上回说。",
        "上回那事，评论区聊得挺热闹，今天再补个后续。",
    ]
    import random
    followup_opener = random.choice(followup_templates)
    followup_opener += "{}"

    new_files = sorted([f for f in os.listdir(LIB) if f.startswith('day')])
    added = 0
    for f in new_files:
        day = int(f.split('_')[0][3:])
        if day <= max_day_before:
            continue
        path = os.path.join(LIB, f)
        d = json.load(open(path, encoding='utf-8'))
        # 打续集标记
        d['is_followup'] = True
        d['followup_of'] = cid
        d['followup_series'] = rec.get('theme', '')
        # 若开头不是续集视角，补上（保持原内容主体不变，续集开场让读者知道是后续）
        content = d.get('content', '')
        if not any(k in content[:20] for k in ['上次', '上回', '接着', '后续']):
            d['content'] = followup_opener.format(content)
            d['content_length'] = len(d['content'])
        json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        added += 1
        print(f"🔗 续集标记: {d['id']} → followup_of={cid}（{d['theme']}）")

    print(f"\n✅ 续集工程完成：新增 {added} 条续集（均标记关联爆款 {cid}，含续集开场视角）")
    print(f"   💡 数据提示：续集内容建议间隔3-5天发布，避免同题材连发触发用户疲劳；发布时优先选晚间黄金档")

if __name__ == "__main__":
    main()
