#!/usr/bin/env python3
"""
微头条内容引擎 - 增强版
支持：next, publish, list, stats, search, quality, export, random, theme
"""
import json
import glob
import os
import sys
import random
from datetime import datetime
from collections import Counter

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(BASE_PATH, "references")

def load_all_contents():
    """加载所有内容"""
    files = sorted(glob.glob(os.path.join(CONTENT_DIR, "day*.json")))
    contents = []
    for f in files:
        with open(f, 'r', encoding='utf-8') as fp:
            contents.append(json.load(fp))
    return contents

def get_next_content():
    """获取下一条待发布内容"""
    contents = load_all_contents()
    pending = [c for c in contents if c.get('status') == 'pending']
    if not pending:
        print("❌ 没有待发布内容了！")
        return None
    pending.sort(key=lambda x: (x['day'], x['number']))
    return pending[0]

def publish_content(day, number):
    """标记内容为已发布"""
    filepath = os.path.join(CONTENT_DIR, f"day{day:02d}_num{number}.json")
    if not os.path.exists(filepath):
        print(f"❌ 找不到内容: day{day:02d}_num{number}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data['status'] = 'published'
    data['published_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已标记为已发布：{data['id']}")
    print(f"   发布时间：{data['published_at']}")
    return True

def list_contents(status=None, theme=None):
    """列出所有内容"""
    contents = load_all_contents()
    if status:
        contents = [c for c in contents if c.get('status') == status]
    if theme:
        contents = [c for c in contents if theme in c.get('theme', '')]
    
    print(f"=== 内容列表（共{len(contents)}条）===")
    for c in contents:
        status_icon = "📝" if c.get('status') == 'pending' else "✅"
        print(f"{status_icon} {c['id']} | {c['content_length']}字 | {c.get('theme','')} | {c['content'][:30]}...")
    return contents

def stats():
    """统计内容库状态"""
    contents = load_all_contents()
    pending = [c for c in contents if c.get('status') == 'pending']
    published = [c for c in contents if c.get('status') == 'published']
    
    print(f"{'='*50}")
    print(f"📊 内容库统计")
    print(f"{'='*50}")
    print(f"总内容: {len(contents)} 条")
    print(f"待发布: {len(pending)} 条 📝")
    print(f"已发布: {len(published)} 条 ✅")
    print()
    
    # 主题统计
    themes = Counter()
    for c in pending:
        main_theme = c.get('theme','').split('+')[0]
        themes[main_theme] += 1
    
    print(f"📂 待发布内容主题分布:")
    for theme, count in themes.most_common():
        bar = "█" * count
        print(f"  {theme:<15} {count:2d}条 {bar}")
    print()
    
    # 字数统计
    if pending:
        lengths = [c['content_length'] for c in pending]
        print(f"📏 字数统计（待发布）:")
        print(f"  最短: {min(lengths)}字")
        print(f"  最长: {max(lengths)}字")
        print(f"  平均: {sum(lengths)//len(lengths)}字")
        print(f"  全部在150字以内: {'✅' if max(lengths) <= 150 else '❌'}")
    print()
    
    # 按天统计
    days = Counter()
    for c in pending:
        days[c['day']] += 1
    print(f"📅 按天分布（共{len(days)}天）:")
    for day in sorted(days.keys()):
        print(f"  Day{day:02d}: {days[day]}条")
    
    # 库存预警
    if len(pending) < 10:
        print(f"\n⚠️  库存预警：待发布内容不足10条，建议补充新内容！")
    elif len(pending) < 20:
        print(f"\n💡 库存提醒：待发布内容{len(pending)}条，可考虑补充新内容。")
    else:
        print(f"\n✅ 库存充足：待发布内容{len(pending)}条，够用约{len(pending)}天（一天1条）。")

def search(keyword):
    """按关键词搜索内容"""
    contents = load_all_contents()
    results = []
    for c in contents:
        if keyword in c.get('content', '') or keyword in c.get('theme', '') or keyword in c.get('title', ''):
            results.append(c)
    
    print(f"🔍 搜索关键词: '{keyword}'")
    print(f"找到 {len(results)} 条内容:")
    print()
    for c in results:
        status_icon = "📝" if c.get('status') == 'pending' else "✅"
        print(f"{status_icon} {c['id']} | {c['content_length']}字 | {c.get('theme','')}")
        print(f"   {c['content'][:60]}...")
        print()
    return results

def quality_check():
    """内容质量检测"""
    contents = load_all_contents()
    pending = [c for c in contents if c.get('status') == 'pending']
    
    print(f"{'='*50}")
    print(f"🔍 内容质量检测")
    print(f"{'='*50}")
    print(f"检测 {len(pending)} 条待发布内容")
    print()
    
    issues = []
    good = 0
    
    for c in pending:
        content = c.get('content', '')
        length = c.get('content_length', 0)
        item_issues = []
        
        # 字数检查
        if length > 150:
            item_issues.append(f"字数超标({length}字)")
        elif length < 80:
            item_issues.append(f"字数偏少({length}字)")
        
        # 开头检查
        first_sentence = content.split('，')[0] if '，' in content else content[:20]
        strong_openers = ['今天', '昨晚', '刚才', '突然', '没想到', '居然', '竟然', '被', '让', '说', '问', '发现', '翻出', '收到', '接到']
        if not any(opener in first_sentence for opener in strong_openers):
            item_issues.append("开头可能不够强")
        
        # 结尾钩子检查
        if not content.endswith('吗？') and not content.endswith('吗?') and '你们' not in content[-20:]:
            item_issues.append("结尾可能缺少评论钩子")
        
        # 35岁元素检查
        if '35岁' not in content:
            item_issues.append("缺少35岁人设元素")
        
        if item_issues:
            issues.append((c['id'], item_issues))
        else:
            good += 1
    
    print(f"✅ 优质内容: {good} 条")
    print(f"⚠️  有改进空间: {len(issues)} 条")
    print()
    
    if issues:
        print(f"📋 改进建议:")
        for cid, item_issues in issues:
            print(f"  {cid}:")
            for issue in item_issues:
                print(f"    - {issue}")
            print()
    
    print(f"{'='*50}")
    if good == len(pending):
        print(f"🎉 所有内容质量优秀！")
    elif good > len(pending) * 0.7:
        print(f"👍 整体质量良好，部分内容可优化。")
    else:
        print(f"💡 建议优化部分内容，提升整体质量。")

def export_markdown():
    """导出内容库为Markdown"""
    contents = load_all_contents()
    pending = [c for c in contents if c.get('status') == 'pending']
    pending.sort(key=lambda x: (x['day'], x['number']))
    
    output = f"# 微头条内容库（待发布）\n\n"
    output += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    output += f"**待发布内容**: {len(pending)} 条\n\n"
    output += f"---\n\n"
    
    current_day = None
    for c in pending:
        if c['day'] != current_day:
            current_day = c['day']
            output += f"## Day {current_day:02d}\n\n"
        
        output += f"### {c['id']} | {c['content_length']}字\n\n"
        output += f"**主题**: {c.get('theme','')}\n\n"
        output += f"**钩子类型**: {c.get('hook_type','')}\n\n"
        output += f"**配图建议**: {c.get('image_suggestion','')}\n\n"
        output += f"**内容**:\n\n{c['content']}\n\n"
        output += f"---\n\n"
    
    filepath = os.path.join(BASE_PATH, "content_library_export.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"✅ 已导出为Markdown: {filepath}")
    print(f"   共 {len(pending)} 条待发布内容")
    return filepath

def random_content():
    """随机取一条待发布内容"""
    contents = load_all_contents()
    pending = [c for c in contents if c.get('status') == 'pending']
    if not pending:
        print("❌ 没有待发布内容了！")
        return None
    
    c = random.choice(pending)
    print(f"🎲 随机内容: {c['id']}")
    print(f"主题: {c.get('theme','')}")
    print(f"字数: {c['content_length']}字")
    print(f"\n内容:\n{c['content']}")
    return c

def theme_list():
    """按主题列出内容"""
    contents = load_all_contents()
    pending = [c for c in contents if c.get('status') == 'pending']
    
    themes = {}
    for c in pending:
        main_theme = c.get('theme','').split('+')[0]
        if main_theme not in themes:
            themes[main_theme] = []
        themes[main_theme].append(c)
    
    print(f"📂 按主题分类（共{len(themes)}个主题）:")
    print()
    for theme, items in sorted(themes.items(), key=lambda x: -len(x[1])):
        print(f"【{theme}】({len(items)}条)")
        for c in items:
            print(f"  {c['id']} | {c['content_length']}字 | {c['content'][:25]}...")
        print()

def smart_pick(day_of_week=None):
    """根据星期几智能选内容
    周一：人情世故/亲戚/同事
    周二：人情世故+职场
    周三：轻松幽默+有反转+有温度（重点发力日）
    周四：轻松幽默
    周五：轻松幽默+周末期待
    周六日：人情世故/情感/轻松
    """
    if day_of_week is None:
        day_of_week = datetime.now().weekday()  # 0=周一, 6=周日
    
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekday_names[day_of_week]
    
    # 主题优先级配置
    theme_priorities = {
        0: ["人情世故", "亲戚", "同事"],  # 周一
        1: ["人情世故", "职场", "同事"],  # 周二
        2: ["幽默", "反转", "温度", "轻松"],  # 周三（重点发力日）
        3: ["幽默", "轻松", "日常"],  # 周四
        4: ["幽默", "周末", "期待", "轻松"],  # 周五
        5: ["人情世故", "情感", "家庭", "轻松"],  # 周六
        6: ["情感", "家庭", "日常", "轻松"],  # 周日
    }
    
    contents = load_all_contents()
    pending = [c for c in contents if c.get('status') == 'pending']
    
    # 主题优先级权重
    priority_themes = theme_priorities.get(day_of_week, [])
    
    # 评分
    scored = []
    for c in pending:
        score = 0
        theme = c.get('theme', '')
        title = c.get('title', '')
        content = c.get('content', '')
        
        # 主题匹配加分
        for i, pt in enumerate(priority_themes):
            if pt in theme or pt in title:
                score += 10 - i  # 越靠前优先级越高
        
        # 深化版加分
        if c.get('deep_version_version') == '2.0':
            score += 5
        
        # 数字细节加分
        import re
        numbers = re.findall(r'\d+', content)
        score += len(numbers) * 2
        
        # 结尾钩子加分
        if content.endswith('吗？') or content.endswith('吗?'):
            score += 3
        
        # 35岁元素加分
        if '35岁' in content:
            score += 2
        
        scored.append((score, c))
    
    # 按分数排序
    scored.sort(key=lambda x: -x[0])
    
    print(f"🤖 智能选内容 - 今天是{weekday}")
    print(f"📋 内容策略: {', '.join(priority_themes[:3])}")
    print(f"📊 候选内容: {len(pending)}条")
    print()
    
    if scored:
        best = scored[0][1]
        print(f"✅ 推荐内容: {best['id']}")
        print(f"   主题: {best.get('theme','')}")
        print(f"   字数: {best['content_length']}字")
        print(f"   匹配度: {scored[0][0]}分")
        print(f"\n--- 内容 ---\n")
        print(best['content'])
        
        # 显示前3名候选
        print(f"\n📋 前3名候选:")
        for i, (score, c) in enumerate(scored[:3]):
            print(f"  {i+1}. {c['id']} | {c.get('theme','')} | {score}分")
        
        return best
    return None

def published_list():
    """列出所有已发布内容"""
    contents = load_all_contents()
    published = [c for c in contents if c.get('status') == 'published']
    published.sort(key=lambda x: x.get('published_at', ''), reverse=True)
    
    print(f"=== 已发布内容列表（共{len(published)}条）===")
    print()
    for c in published:
        print(f"✅ {c['id']} | {c.get('published_at','')[:10]} | {c['content_length']}字 | {c.get('theme','')[:20]}")
        print(f"   {c['content'][:40]}...")
        print()
    
    return published

def check_duplicates():
    """检查内容重复"""
    contents = load_all_contents()
    
    # 按内容相似度检查
    seen = {}
    duplicates = []
    
    for c in contents:
        content = c.get('content', '')
        # 取前30字作为指纹
        fingerprint = content[:30]
        if fingerprint in seen:
            duplicates.append((seen[fingerprint], c))
        else:
            seen[fingerprint] = c
    
    print(f"🔍 重复内容检查")
    print(f"总内容: {len(contents)}条")
    print(f"重复内容: {len(duplicates)}对")
    print()
    
    if duplicates:
        print(f"⚠️  发现重复内容:")
        for c1, c2 in duplicates:
            print(f"  {c1['id']} <-> {c2['id']}")
            print(f"    状态: {c1.get('status')} / {c2.get('status')}")
            print(f"    {c1['content'][:40]}...")
            print()
    else:
        print(f"✅ 没有发现重复内容")
    
    return duplicates

def mark_published_by_id(content_id):
    """通过ID标记内容为已发布"""
    contents = load_all_contents()
    for c in contents:
        if c.get('id') == content_id:
            return publish_content(c['day'], c['number'])
    print(f"❌ 找不到内容: {content_id}")
    return False

def main():
    if len(sys.argv) < 2:
        print("用法: python content_engine.py <command> [options]")
        print()
        print("命令:")
        print("  next              获取下一条待发布内容")
        print("  smart             智能选内容（根据星期几自动选）")
        print("  publish           标记内容为已发布 (--day N --number N 或 --id P01_d39_n1)")
        print("  list              列出所有内容 (--status pending/published --theme 关键词)")
        print("  published         列出所有已发布内容")
        print("  stats             统计内容库状态")
        print("  search            按关键词搜索内容 (关键词)")
        print("  quality           内容质量检测")
        print("  duplicates        检查内容重复")
        print("  export            导出内容库为Markdown")
        print("  random            随机取一条待发布内容")
        print("  theme             按主题列出内容")
        print()
        print("示例:")
        print("  python content_engine.py next")
        print("  python content_engine.py publish --day 12 --number 1")
        print("  python content_engine.py list --status pending")
        print("  python content_engine.py stats")
        print("  python content_engine.py search 外卖")
        print("  python content_engine.py quality")
        return
    
    command = sys.argv[1]
    
    if command == 'next':
        content = get_next_content()
        if content:
            print(f"=== 下一条待发布内容 ===")
            print(f"ID：{content['id']}")
            print(f"第{content['day']}天 第{content['number']}条")
            print(f"标题：{content['title']}")
            print(f"主题：{content.get('theme','')}")
            print(f"钩子类型：{content.get('hook_type','')}")
            print(f"配图建议：{content.get('image_suggestion','')}")
            print(f"\n--- 内容 ---\n")
            print(content['content'])
            print(f"\n字数：{content['content_length']}")
    
    elif command == 'smart':
        smart_pick()
    
    elif command == 'publish':
        # 支持 --id P01_d39_n1 格式
        content_id = None
        day = None
        number = None
        for i, arg in enumerate(sys.argv):
            if arg == '--id' and i+1 < len(sys.argv):
                content_id = sys.argv[i+1]
            if arg == '--day' and i+1 < len(sys.argv):
                day = int(sys.argv[i+1])
            if arg == '--number' and i+1 < len(sys.argv):
                number = int(sys.argv[i+1])
        
        if content_id:
            mark_published_by_id(content_id)
        elif day is not None and number is not None:
            publish_content(day, number)
        else:
            print("❌ 需要 --id P01_d39_n1 或 --day 和 --number 参数")
            return
    
    elif command == 'published':
        published_list()
    
    elif command == 'list':
        status = None
        theme = None
        for i, arg in enumerate(sys.argv):
            if arg == '--status' and i+1 < len(sys.argv):
                status = sys.argv[i+1]
            if arg == '--theme' and i+1 < len(sys.argv):
                theme = sys.argv[i+1]
        list_contents(status, theme)
    
    elif command == 'stats':
        stats()
    
    elif command == 'search':
        if len(sys.argv) < 3:
            print("❌ 需要搜索关键词")
            return
        search(sys.argv[2])
    
    elif command == 'quality':
        quality_check()
    
    elif command == 'duplicates':
        check_duplicates()
    
    elif command == 'export':
        export_markdown()
    
    elif command == 'random':
        random_content()
    
    elif command == 'theme':
        theme_list()
    
    else:
        print(f"❌ 未知命令: {command}")
        print("使用 'python content_engine.py' 查看帮助")

if __name__ == '__main__':
    main()
