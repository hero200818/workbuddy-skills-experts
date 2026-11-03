#!/usr/bin/env python3
"""
生成HTML数据看板 - 可视化展示账号运营数据
"""
import csv
import os
import json
from datetime import datetime

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_PATH, "references", "perfomance_tracking.csv")
OUTPUT_FILE = os.path.join(BASE_PATH, "dashboard.html")

def safe_int(value, default=0):
    try:
        return int(float(value or 0))
    except:
        return default

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def generate_dashboard():
    data = load_data()
    
    # 计算统计数据
    total_impressions = sum(safe_int(d['展现量']) for d in data)
    total_reads = sum(safe_int(d['阅读量']) for d in data)
    total_comments = sum(safe_int(d['评论量']) for d in data)
    total_likes = sum(safe_int(d['点赞量']) for d in data)
    avg_ctr = total_reads / total_impressions * 100 if total_impressions > 0 else 0
    
    # 按主题统计
    theme_stats = {}
    for d in data:
        theme = d['主题'].split('+')[0].split('/')[0]
        if theme not in theme_stats:
            theme_stats[theme] = {'count': 0, 'impressions': 0, 'reads': 0}
        theme_stats[theme]['count'] += 1
        theme_stats[theme]['impressions'] += safe_int(d['展现量'])
        theme_stats[theme]['reads'] += safe_int(d['阅读量'])
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微爆工坊数据看板</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f7fa; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; margin-bottom: 20px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 30px; }}
        .stat-card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .stat-card .label {{ color: #666; font-size: 14px; margin-bottom: 8px; }}
        .stat-card .value {{ color: #333; font-size: 28px; font-weight: bold; }}
        .stat-card .sub {{ color: #999; font-size: 12px; margin-top: 4px; }}
        .section {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .section h2 {{ color: #333; margin-bottom: 16px; font-size: 18px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ color: #666; font-weight: 600; font-size: 14px; }}
        tr:hover {{ background: #f9f9f9; }}
        .hot {{ color: #ff4757; font-weight: bold; }}
        .good {{ color: #2ed573; }}
        .theme-bar {{ height: 8px; background: #f0f0f0; border-radius: 4px; margin-top: 4px; }}
        .theme-bar-fill {{ height: 100%; background: linear-gradient(90deg, #ff6b6b, #ee5a24); border-radius: 4px; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 微爆工坊数据看板</h1>
        <p style="color:#666;margin-bottom:20px;">更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">总展现量</div>
                <div class="value">{total_impressions:,}</div>
                <div class="sub">{len(data)}条内容</div>
            </div>
            <div class="stat-card">
                <div class="label">总阅读量</div>
                <div class="value">{total_reads:,}</div>
                <div class="sub">平均点击率 {avg_ctr:.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="label">总评论</div>
                <div class="value">{total_comments:,}</div>
                <div class="sub">平均每条 {total_comments//len(data) if data else 0} 条</div>
            </div>
            <div class="stat-card">
                <div class="label">总点赞</div>
                <div class="value">{total_likes:,}</div>
                <div class="sub">粉丝互动好</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🔥 主题表现排名</h2>
            <table>
                <thead>
                    <tr>
                        <th>主题</th>
                        <th>条数</th>
                        <th>总展现</th>
                        <th>平均展现</th>
                        <th>表现</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # 按展现排序
    sorted_themes = sorted(theme_stats.items(), key=lambda x: -x[1]['impressions'])
    max_impressions = max((s['impressions'] for s in theme_stats.values()), default=1)
    
    for theme, stats in sorted_themes:
        avg_imp = stats['impressions'] // stats['count']
        bar_width = int(stats['impressions'] / max_impressions * 100)
        hot_class = 'hot' if avg_imp > 100000 else 'good'
        html += f"""
                    <tr>
                        <td><strong>{theme}</strong></td>
                        <td>{stats['count']}</td>
                        <td>{stats['impressions']:,}</td>
                        <td class="{hot_class}">{avg_imp:,}</td>
                        <td>
                            <div class="theme-bar">
                                <div class="theme-bar-fill" style="width:{bar_width}%"></div>
                            </div>
                        </td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>📝 内容明细</h2>
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>内容ID</th>
                        <th>主题</th>
                        <th>展现</th>
                        <th>阅读</th>
                        <th>点击率</th>
                        <th>评论</th>
                        <th>点赞</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for d in data:
        impressions = safe_int(d['展现量'])
        ctr_class = 'hot' if impressions > 100000 else ''
        html += f"""
                    <tr>
                        <td>{d['发布日期']}</td>
                        <td>{d['内容ID']}</td>
                        <td>{d['主题']}</td>
                        <td class="{ctr_class}">{impressions:,}</td>
                        <td>{safe_int(d['阅读量']):,}</td>
                        <td>{d['点击率']}</td>
                        <td>{d['评论量']}</td>
                        <td>{d['点赞量']}</td>
                    </tr>
        """
    
    html += f"""
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>💡 运营建议</h2>
            <ul style="color:#666;line-height:2;">
                <li>✅ 加大<b>{sorted_themes[0][0] if sorted_themes else '工资'}</b>主题比重，爆款潜力最高</li>
                <li>✅ 保持晚间20:00发布，数据验证效果好</li>
                <li>✅ 内容控制在120-140字，点击率最高</li>
                <li>✅ 结尾一定要留评论钩子，互动率提升明显</li>
                <li>📈 数据积累越多，系统推荐越精准</li>
            </ul>
        </div>
        
        <div class="footer">
            微爆工坊 v3.0 - 数据驱动的爆款微头条生产系统
        </div>
    </div>
</body>
</html>
    """
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 数据看板已生成: {OUTPUT_FILE}")
    return OUTPUT_FILE

if __name__ == '__main__':
    generate_dashboard()
