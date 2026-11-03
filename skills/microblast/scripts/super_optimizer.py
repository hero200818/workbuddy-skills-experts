#!/usr/bin/env python3
"""
超级运营优化器 - 爆款预测、粉丝增长分析、收益优化
"""
import csv
import os
import sys
import json
from datetime import datetime
from collections import defaultdict

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_PATH, "references", "perfomance_tracking.csv")

def safe_int(value, default=0):
    try:
        return int(float(value or 0))
    except:
        return default

def safe_float(value, default=0.0):
    try:
        return float(str(value).replace('%', '') or 0)
    except:
        return default

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def predict_hot(content_id=None, content_text=None, theme=None):
    """爆款预测模型 - 发布前预测这条内容的表现"""
    print(f"{'='*60}")
    print(f"🔮 爆款预测模型")
    print(f"{'='*60}")
    
    # 读取历史数据作为训练集
    data = load_data()
    if len(data) < 2:
        print("⚠️  数据样本太少，预测仅供参考")
        print(f"   当前样本: {len(data)}条")
        print()
    
    # 如果传入了内容ID，从内容库读取
    content = content_text
    if content_id:
        content_dir = os.path.join(BASE_PATH, "references")
        for f in os.listdir(content_dir):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(content_dir, f), 'r', encoding='utf-8') as fp:
                        c = json.load(fp)
                    if c.get('id') == content_id:
                        content = c['content']
                        theme = c.get('theme', theme)
                        break
                except:
                    pass
    
    if not content:
        print("❌ 需要传入内容ID或内容文本")
        return
    
    print(f"📝 预测内容: {content[:50]}...")
    print()
    
    # 预测维度评分
    scores = {}
    
    # 1. 主题匹配度（根据历史爆款主题）
    theme_score = 50  # 基础分
    hot_themes = {
        '工资': 30, '收入': 30, '省钱': 25,
        '人情世故': 20, '亲戚': 25,
        '35岁': 25, '裁员': 20, '职场': 15,
        '外卖': 15, '家庭': 10
    }
    if theme:
        for k, v in hot_themes.items():
            if k in theme:
                theme_score += v
    scores['主题匹配'] = min(theme_score, 100)
    
    # 2. 开头吸引力（前20字有没有钩子）
    opening = content[:20]
    opening_score = 50
    import re
    if re.search(r'\d+[块万千年月天]', opening):
        opening_score += 30  # 数字钩子
    if any(w in opening for w in ['今天', '刚才', '结果', '没想到', '但是']):
        opening_score += 20  # 冲突钩子
    scores['开头吸引力'] = min(opening_score, 100)
    
    # 3. 结尾互动性（有没有评论钩子）
    ending = content[-30:]
    ending_score = 50
    if '？' in ending or '吗' in ending or '呢' in ending:
        ending_score += 30  # 有问题
    if '你们' in ending or '你呢' in ending:
        ending_score += 20  # 引导互动
    scores['结尾互动'] = min(ending_score, 100)
    
    # 4. 字数合适度
    length = len(content)
    length_score = 50
    if 100 <= length <= 140:
        length_score = 90  # 黄金区间
    elif 80 <= length <= 150:
        length_score = 70
    else:
        length_score = 40
    scores['字数合适'] = length_score
    
    # 5. 细节丰富度
    detail_score = 50
    if re.search(r'\d+[块元分钟]', content):
        detail_score += 20  # 有具体数字
    if '说' in content or '道' in content:
        detail_score += 15  # 有对话
    if any(w in content for w in ['啊', '呢', '吧', '嘛']):
        detail_score += 15  # 口语化
    scores['细节丰富'] = min(detail_score, 100)
    
    # 计算总分
    weights = {'主题匹配': 0.3, '开头吸引力': 0.25, '结尾互动': 0.2, '字数合适': 0.1, '细节丰富': 0.15}
    total_score = sum(scores[k] * weights[k] for k in scores)
    
    print(f"📊 预测评分:")
    for k, v in scores.items():
        bar = '█' * (v // 10)
        print(f"  {k:<10} {v}分 {bar}")
    print()
    
    print(f"📈 综合得分: {total_score:.1f}/100")
    print()
    
    # 预测结果
    if total_score >= 85:
        level = "🏆 S级（爆款相！）"
        prediction = "预计展现: 50万-100万+"
        tip = "赶紧发！这数据绝对爆"
    elif total_score >= 75:
        level = "🥇 A级（优质内容）"
        prediction = "预计展现: 10万-50万"
        tip = "可以发，有爆款潜力"
    elif total_score >= 60:
        level = "🥈 B级（一般内容）"
        prediction = "预计展现: 1万-10万"
        tip = "可以发，但建议优化开头"
    else:
        level = "🥉 C级（待改进）"
        prediction = "预计展现: <1万"
        tip = "建议重写后再发"
    
    print(f"预测等级: {level}")
    print(f"预测效果: {prediction}")
    print(f"运营建议: {tip}")
    
    return total_score

def fan_growth_analysis():
    """粉丝增长分析 - 分析哪条内容涨粉最多"""
    data = load_data()
    
    print(f"{'='*60}")
    print(f"👥 粉丝增长分析")
    print(f"{'='*60}")
    print(f"样本: {len(data)} 条内容")
    print()
    
    # 按涨粉排序
    sorted_data = sorted(data, key=lambda x: -safe_int(x['净增粉丝']))
    
    print(f"📈 涨粉最多的内容排名:")
    print(f"{'内容ID':<15} {'主题':<20} {'展现':<10} {'涨粉':<6} {'涨粉率'}")
    print(f"{'-'*65}")
    
    for d in sorted_data[:5]:
        impressions = safe_int(d['展现量'])
        fans = safe_int(d['净增粉丝'])
        rate = fans / impressions * 10000 if impressions > 0 else 0
        print(f"{d['内容ID']:<15} {d['主题'][:18]:<20} {impressions:<10,} {fans:<6} {rate:.2f}‱")
    
    print()
    
    # 找涨粉率最高的主题
    theme_fans = defaultdict(lambda: {'count': 0, 'fans': 0, 'impressions': 0})
    for d in data:
        theme = d['主题'].split('+')[0].split('/')[0]
        theme_fans[theme]['count'] += 1
        theme_fans[theme]['fans'] += safe_int(d['净增粉丝'])
        theme_fans[theme]['impressions'] += safe_int(d['展现量'])
    
    print(f"🎯 各主题涨粉效率:")
    for theme, stats in sorted(theme_fans.items(), key=lambda x: -x[1]['fans']/x[1]['impressions'] if x[1]['impressions']>0 else 0):
        rate = stats['fans'] / stats['impressions'] * 10000 if stats['impressions'] > 0 else 0
        print(f"  {theme:<15} 每万展现涨粉 {rate:.2f}人")
    
    print()
    print(f"💡 粉丝增长建议:")
    print(f"  1. 涨粉多的主题，系统会持续推流，要多写")
    print(f"  2. 涨粉率高的内容，说明粉丝认可，要保持风格")
    print(f"  3. 互动率高的内容，涨粉也多，结尾一定要留钩子")

def revenue_analysis():
    """收益优化分析 - 分析哪条内容收益最高"""
    data = load_data()
    
    print(f"{'='*60}")
    print(f"💰 收益优化分析")
    print(f"{'='*60}")
    
    total_revenue = sum(safe_float(d['创作收益']) for d in data)
    total_impressions = sum(safe_int(d['展现量']) for d in data)
    avg_cpm = total_revenue / total_impressions * 1000 if total_impressions > 0 else 0
    
    print(f"总收益: {total_revenue:.2f}元")
    print(f"总展现: {total_impressions:,}")
    print(f"平均千次展现收益(CPM): {avg_cpm:.2f}元")
    print()
    
    # 按收益排序
    sorted_data = sorted(data, key=lambda x: -safe_float(x['创作收益']))
    
    print(f"💵 收益最高的内容排名:")
    print(f"{'内容ID':<15} {'主题':<20} {'展现':<10} {'收益':<8} {'CPM'}")
    print(f"{'-'*65}")
    
    for d in sorted_data[:5]:
        impressions = safe_int(d['展现量'])
        revenue = safe_float(d['创作收益'])
        cpm = revenue / impressions * 1000 if impressions > 0 else 0
        print(f"{d['内容ID']:<15} {d['主题'][:18]:<20} {impressions:<10,} {revenue:<8.2f} {cpm:.2f}元")
    
    print()
    
    # 找CPM最高的主题
    theme_cpm = defaultdict(lambda: {'count': 0, 'revenue': 0, 'impressions': 0})
    for d in data:
        theme = d['主题'].split('+')[0].split('/')[0]
        theme_cpm[theme]['count'] += 1
        theme_cpm[theme]['revenue'] += safe_float(d['创作收益'])
        theme_cpm[theme]['impressions'] += safe_int(d['展现量'])
    
    print(f"📊 各主题收益效率(CPM):")
    for theme, stats in sorted(theme_cpm.items(), key=lambda x: -x[1]['revenue']/x[1]['impressions'] if x[1]['impressions']>0 else 0):
        cpm = stats['revenue'] / stats['impressions'] * 1000 if stats['impressions'] > 0 else 0
        print(f"  {theme:<15} CPM {cpm:.2f}元/千次")
    
    print()
    print(f"💡 收益优化建议:")
    print(f"  1. CPM高的主题，同样展现赚更多钱，要多写")
    print(f"  2. 展现量是收益基础，先求大展现再求CPM")
    print(f"  3. 互动率高的内容，推荐流量多，收益也高")

def main():
    if len(sys.argv) < 2:
        print("用法: python super_optimizer.py <command>")
        print()
        print("命令:")
        print("  predict <内容ID或内容文本>    爆款预测")
        print("  fans                          粉丝增长分析")
        print("  revenue                       收益优化分析")
        print("  all                           全部分析")
        print()
        print("示例:")
        print("  python super_optimizer.py predict P01_d45_n2")
        print("  python super_optimizer.py fans")
        print("  python super_optimizer.py all")
        return
    
    command = sys.argv[1]
    
    if command == 'predict':
        arg = sys.argv[2] if len(sys.argv) > 2 else None
        if arg and arg.startswith('P01'):
            predict_hot(content_id=arg)
        else:
            predict_hot(content_text=arg)
    
    elif command == 'fans':
        fan_growth_analysis()
    
    elif command == 'revenue':
        revenue_analysis()
    
    elif command == 'all':
        fan_growth_analysis()
        print()
        revenue_analysis()
    
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == '__main__':
    main()
