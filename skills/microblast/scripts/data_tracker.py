#!/usr/bin/env python3
"""
数据追踪与分析系统
支持：record, list, analyze, weekly, export
"""
import csv
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_PATH, "references", "perfomance_tracking.csv")

FIELDS = ['发布日期', '内容ID', '主题', '字数', '发布时间', '展现量', '阅读量', 
          '点击率', '平均阅读时长', '评论量', '点赞量', '收藏量', '转发量', 
          '净增粉丝', '创作收益', '备注']

def safe_int(value, default=0):
    """安全转换为整数"""
    try:
        return int(value or 0)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """安全转换为浮点数"""
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return default

def load_data():
    """加载数据"""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_data(data):
    """保存数据"""
    with open(DATA_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(data)

def record_data_interactive():
    """记录一条内容的数据（交互式）"""
    print("📝 记录内容数据（交互式）")
    print("="*50)
    
    record = {}
    record['发布日期'] = input("发布日期 (YYYY-MM-DD，默认今天): ").strip() or datetime.now().strftime('%Y-%m-%d')
    record['内容ID'] = input("内容ID (如 P01_d12_n1): ").strip()
    record['主题'] = input("主题: ").strip()
    record['字数'] = input("字数: ").strip()
    record['发布时间'] = input("发布时间 (HH:MM): ").strip()
    record['展现量'] = input("展现量: ").strip()
    record['阅读量'] = input("阅读量: ").strip()
    record['点击率'] = input("点击率 (如 17.4%): ").strip()
    record['平均阅读时长'] = input("平均阅读时长 (如 26秒): ").strip()
    record['评论量'] = input("评论量: ").strip()
    record['点赞量'] = input("点赞量: ").strip()
    record['收藏量'] = input("收藏量: ").strip()
    record['转发量'] = input("转发量: ").strip()
    record['净增粉丝'] = input("净增粉丝: ").strip()
    record['创作收益'] = input("创作收益 (元): ").strip()
    record['备注'] = input("备注: ").strip()
    
    data = load_data()
    data.append(record)
    save_data(data)
    
    print(f"\n✅ 已记录: {record['内容ID']}")
    print(f"   展现: {record['展现量']} | 阅读: {record['阅读量']} | 点击率: {record['点击率']}")

def record_data_auto(content_id, views, comments, likes):
    """记录一条内容的数据（自动/非交互式）"""
    # 从内容库读取内容信息
    import json
    import glob
    
    content_file = None
    for f in glob.glob(os.path.join(BASE_PATH, "references", "*.json")):
        with open(f, 'r', encoding='utf-8') as fp:
            c = json.load(fp)
            if c.get('id') == content_id:
                content_file = c
                break
    
    if not content_file:
        print(f"❌ 找不到内容: {content_id}")
        return False
    
    record = {}
    record['发布日期'] = content_file.get('published_at', datetime.now().strftime('%Y-%m-%d'))[:10]
    record['内容ID'] = content_id
    record['主题'] = content_file.get('theme', '')
    record['字数'] = str(content_file.get('content_length', 0))
    record['发布时间'] = content_file.get('published_at', '')[11:16]
    record['展现量'] = str(views)
    record['阅读量'] = str(int(views * 0.1))  # 估算
    record['点击率'] = f"{views/int(views)*100:.1f}%" if views else "0%"
    record['平均阅读时长'] = ""
    record['评论量'] = str(comments)
    record['点赞量'] = str(likes)
    record['收藏量'] = "0"
    record['转发量'] = "0"
    record['净增粉丝'] = "0"
    record['创作收益'] = ""
    record['备注'] = "自动记录"
    
    data = load_data()
    # 检查是否已存在
    existing = [d for d in data if d['内容ID'] == content_id]
    if existing:
        print(f"⚠️  内容 {content_id} 已存在数据，跳过")
        return False
    
    data.append(record)
    save_data(data)
    
    print(f"✅ 已记录: {content_id}")
    print(f"   展现: {views} | 评论: {comments} | 点赞: {likes}")
    return True

def list_data():
    """列出所有数据"""
    data = load_data()
    if not data:
        print("❌ 暂无数据")
        return
    
    print(f"📊 数据列表（共{len(data)}条）")
    print("="*80)
    print(f"{'日期':<12} {'内容ID':<15} {'主题':<15} {'展现':<8} {'阅读':<8} {'点击率':<8} {'评论':<5} {'点赞':<5}")
    print("-"*80)
    for d in data:
        print(f"{d['发布日期']:<12} {d['内容ID']:<15} {d['主题'][:13]:<15} {d['展现量']:<8} {d['阅读量']:<8} {d['点击率']:<8} {d['评论量']:<5} {d['点赞量']:<5}")

def analyze_data():
    """分析数据"""
    data = load_data()
    if not data:
        print("❌ 暂无数据")
        return
    
    print(f"{'='*60}")
    print(f"📈 数据分析报告")
    print(f"{'='*60}")
    print(f"统计周期: {data[0]['发布日期']} ~ {data[-1]['发布日期']}")
    print(f"总发布数: {len(data)} 条")
    print()
    
    # 总体统计
    total_impressions = sum(safe_int(d['展现量']) for d in data)
    total_reads = sum(safe_int(d['阅读量']) for d in data)
    total_comments = sum(safe_int(d['评论量']) for d in data)
    total_likes = sum(safe_int(d['点赞量']) for d in data)
    total_fans = sum(safe_int(d['净增粉丝']) for d in data)
    total_revenue = sum(safe_float(d['创作收益']) for d in data)
    
    avg_ctr = total_reads / total_impressions * 100 if total_impressions > 0 else 0
    
    print(f"📊 总体统计:")
    print(f"  总展现量: {total_impressions:,}")
    print(f"  总阅读量: {total_reads:,}")
    print(f"  平均点击率: {avg_ctr:.1f}%")
    print(f"  总评论量: {total_comments}")
    print(f"  总点赞量: {total_likes}")
    print(f"  净增粉丝: {total_fans}")
    print(f"  总收益: {total_revenue:.2f}元")
    print()
    
    # 按主题分析
    print(f"📂 按主题分析:")
    theme_stats = defaultdict(lambda: {'count': 0, 'impressions': 0, 'reads': 0, 'comments': 0, 'likes': 0})
    for d in data:
        theme = d['主题'].split('+')[0]
        theme_stats[theme]['count'] += 1
        theme_stats[theme]['impressions'] += safe_int(d['展现量'])
        theme_stats[theme]['reads'] += safe_int(d['阅读量'])
        theme_stats[theme]['comments'] += safe_int(d['评论量'])
        theme_stats[theme]['likes'] += safe_int(d['点赞量'])
    
    print(f"  {'主题':<15} {'条数':<5} {'总展现':<10} {'总阅读':<10} {'平均点击率':<10} {'评论':<6} {'点赞':<6}")
    print(f"  {'-'*65}")
    for theme, stats in sorted(theme_stats.items(), key=lambda x: -x[1]['impressions']):
        ctr = stats['reads'] / stats['impressions'] * 100 if stats['impressions'] > 0 else 0
        print(f"  {theme:<15} {stats['count']:<5} {stats['impressions']:<10,} {stats['reads']:<10,} {ctr:<10.1f}% {stats['comments']:<6} {stats['likes']:<6}")
    print()
    
    # 爆款识别
    print(f"🔥 爆款内容（展现>1万）:")
    hot = [d for d in data if safe_int(d['展现量']) > 10000]
    if hot:
        for d in hot:
            print(f"  ✅ {d['内容ID']} | {d['主题']} | 展现{d['展现量']} | 点击率{d['点击率']} | {d.get('备注','')}")
    else:
        print("  暂无爆款内容")
    print()
    
    # 低表现内容
    print(f"⚠️  低表现内容（展现<1000）:")
    low = [d for d in data if safe_int(d['展现量']) < 1000]
    if low:
        for d in low:
            print(f"  ⚠️  {d['内容ID']} | {d['主题']} | 展现{d['展现量']} | 点击率{d['点击率']}")
    else:
        print("  暂无低表现内容")
    print()
    
    # 建议
    print(f"💡 优化建议:")
    if avg_ctr > 15:
        print(f"  ✅ 整体点击率优秀({avg_ctr:.1f}%)，继续保持当前内容风格")
    elif avg_ctr > 10:
        print(f"  👍 整体点击率良好({avg_ctr:.1f}%)，可优化开头提升点击率")
    else:
        print(f"  ⚠️  整体点击率偏低({avg_ctr:.1f}%)，建议优化开头和选题")
    
    best_theme = max(theme_stats.items(), key=lambda x: x[1]['impressions'])[0]
    print(f"  📌 表现最好的主题: {best_theme}，建议多发布此类内容")
    
    if len(hot) > 0:
        print(f"  🎯 已有{len(hot)}条爆款，分析爆款特征并复制成功公式")

def weekly_report():
    """生成周报"""
    data = load_data()
    if not data:
        print("❌ 暂无数据")
        return
    
    # 取最近7天的数据
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    week_data = [d for d in data if datetime.strptime(d['发布日期'], '%Y-%m-%d') >= week_ago]
    
    print(f"{'='*60}")
    print(f"📅 周度报告（{week_ago.strftime('%Y-%m-%d')} ~ {today.strftime('%Y-%m-%d')}）")
    print(f"{'='*60}")
    
    if not week_data:
        print("本周暂无发布数据")
        return
    
    print(f"本周发布: {len(week_data)} 条")
    
    total_impressions = sum(safe_int(d['展现量']) for d in week_data)
    total_reads = sum(safe_int(d['阅读量']) for d in week_data)
    total_comments = sum(safe_int(d['评论量']) for d in week_data)
    total_likes = sum(safe_int(d['点赞量']) for d in week_data)
    total_fans = sum(safe_int(d['净增粉丝']) for d in week_data)
    
    avg_ctr = total_reads / total_impressions * 100 if total_impressions > 0 else 0
    
    print(f"总展现: {total_impressions:,} | 总阅读: {total_reads:,} | 平均点击率: {avg_ctr:.1f}%")
    print(f"总评论: {total_comments} | 总点赞: {total_likes} | 净增粉丝: {total_fans}")
    print()
    
    print("📋 本周内容明细:")
    for d in week_data:
        print(f"  {d['发布日期']} {d['内容ID']} | {d['主题'][:15]} | 展现{d['展现量']} | 点击率{d['点击率']} | 评论{d['评论量']}")

def export_markdown():
    """导出为Markdown报告"""
    data = load_data()
    if not data:
        print("❌ 暂无数据")
        return
    
    output = f"# 微头条数据追踪报告\n\n"
    output += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    output += f"**总发布数**: {len(data)} 条\n\n"
    output += f"---\n\n"
    
    output += f"## 数据明细\n\n"
    output += f"| 日期 | 内容ID | 主题 | 字数 | 展现 | 阅读 | 点击率 | 评论 | 点赞 | 收藏 | 净增粉 | 收益 | 备注 |\n"
    output += f"|------|--------|------|------|------|------|--------|------|------|------|--------|------|------|\n"
    
    for d in data:
        output += f"| {d['发布日期']} | {d['内容ID']} | {d['主题']} | {d['字数']} | {d['展现量']} | {d['阅读量']} | {d['点击率']} | {d['评论量']} | {d['点赞量']} | {d['收藏量']} | {d['净增粉丝']} | {d['创作收益']} | {d.get('备注','')} |\n"
    
    filepath = os.path.join(BASE_PATH, "references", "data_report.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"✅ 已导出为Markdown: {filepath}")

def main():
    if len(sys.argv) < 2:
        print("用法: python data_tracker.py <command>")
        print()
        print("命令:")
        print("  record     记录一条内容的数据（交互式）")
        print("  record-auto 自动记录数据 (--id 内容ID --views 展现 --comments 评论 --likes 点赞)")
        print("  list       列出所有数据")
        print("  analyze    分析数据")
        print("  weekly     生成周报")
        print("  export     导出为Markdown报告")
        print()
        print("示例:")
        print("  python data_tracker.py record")
        print("  python data_tracker.py record-auto --id P01_d33_n3 --views 977918 --comments 96 --likes 414")
        print("  python data_tracker.py list")
        print("  python data_tracker.py analyze")
        print("  python data_tracker.py weekly")
        return
    
    command = sys.argv[1]
    
    if command == 'record':
        record_data_interactive()
    
    elif command == 'record-auto':
        content_id = None
        views = 0
        comments = 0
        likes = 0
        for i, arg in enumerate(sys.argv):
            if arg == '--id' and i+1 < len(sys.argv):
                content_id = sys.argv[i+1]
            if arg == '--views' and i+1 < len(sys.argv):
                views = int(sys.argv[i+1])
            if arg == '--comments' and i+1 < len(sys.argv):
                comments = int(sys.argv[i+1])
            if arg == '--likes' and i+1 < len(sys.argv):
                likes = int(sys.argv[i+1])
        
        if not content_id:
            print("❌ 需要 --id 参数")
        else:
            record_data_auto(content_id, views, comments, likes)
    elif command == 'list':
        list_data()
    elif command == 'analyze':
        analyze_data()
    elif command == 'weekly':
        weekly_report()
    elif command == 'export':
        export_markdown()
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == '__main__':
    main()
