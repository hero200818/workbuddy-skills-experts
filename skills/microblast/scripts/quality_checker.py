#!/usr/bin/env python3
"""
内容质量检查器 - 自动检查内容是否符合爆款v3.0标准
发布前一键检查，避免发出去才发现问题
"""
import json
import os
import sys
import re

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def check_content(content):
    """检查单条内容质量，返回得分和问题列表"""
    issues = []
    score = 100
    
    # 1. 字数检查（100-150字最佳）
    length = len(content)
    if length < 80:
        issues.append(f"❌ 字数太少：{length}字（建议100-150字）")
        score -= 15
    elif length > 150:
        issues.append(f"❌ 字数太多：{length}字（建议150字以内）")
        score -= 20
    elif 100 <= length <= 140:
        issues.append(f"✅ 字数合适：{length}字（黄金区间）")
    else:
        issues.append(f"⚠️  字数：{length}字（建议100-140字）")
        score -= 5
    
    # 2. 开头检查（前20字要有钩子）
    opening = content[:20]
    has_hook = False
    
    # 强数字开头
    if re.search(r'\d+[块万千年月天]', opening):
        issues.append(f"✅ 开头有数字钩子：'{opening[:15]}...'")
        has_hook = True
        score += 5
    
    # 强冲突开头
    conflict_words = ['但是', '可是', '没想到', '结果', '今天', '刚才']
    if any(w in opening for w in conflict_words):
        issues.append(f"✅ 开头有冲突感：'{opening[:15]}...'")
        has_hook = True
    
    if not has_hook:
        issues.append(f"⚠️  开头不够抓眼球，建议加数字或冲突")
        score -= 10
    
    # 3. 结尾检查（有没有评论钩子）
    ending = content[-30:]
    has_question = '？' in ending or '吗' in ending or '呢' in ending
    if has_question:
        issues.append(f"✅ 结尾有评论钩子：'{ending[-15:]}'")
        score += 5
    else:
        issues.append(f"⚠️  结尾没有评论钩子，建议加个问题")
        score -= 10
    
    # 4. 有没有具体细节（数字、场景、对话）
    has_detail = False
    if re.search(r'\d+[块元分钟%]', content):
        issues.append(f"✅ 有具体数字细节")
        has_detail = True
    if '，' in content or '。' in content:
        # 检查有没有对话感
        if '说' in content or '道' in content:
            issues.append(f"✅ 有对话感")
            has_detail = True
    
    if not has_detail:
        issues.append(f"⚠️  缺少具体细节，建议加数字/场景/对话")
        score -= 10
    
    # 4.5 生理反应检查（共鸣关键）
    body_words = ['心里', '喉咙', '鼻子', '手心', '胃', '眼睛', '脸红', '喘', '叹气', '愣', '沉默', '发紧', '酸', '凉', '堵']
    body_hit = [w for w in body_words if w in content]
    if body_hit:
        issues.append(f"✅ 有生理反应（{'/'.join(body_hit[:3])}）——共鸣关键")
        score += 5
    else:
        issues.append(f"⚠️  缺少生理反应，建议加：喉咙发紧/鼻子一酸/手心发凉")
        score -= 8
    
    # 5. 检查有没有AI味（加强版）
    ai_phrases = ['综上所述', '总而言之', '值得注意的是', '在这个', '我们可以看到', '众所周知', '另外', '此外', '其次', '总的来说', '一定程度上', '某种程度上', '这不仅仅是', '更是', '希望我们', '相信大家']
    has_ai = any(p in content for p in ai_phrases)
    if has_ai:
        issues.append(f"❌ 有AI味词汇，建议删掉")
        score -= 20
    else:
        issues.append(f"✅ 无AI味词汇")
    
    # 5.5 禁词检查（引导关注/点赞等）
    forbidden = ['关注我', '点赞收藏', '双击', '转发给', '评论区告诉我', '支持一下', '记得关注', '点个关注', '求关注', '求点赞']
    has_forbidden = [w for w in forbidden if w in content]
    if has_forbidden:
        issues.append(f"❌ 含违规引导词：{'/'.join(has_forbidden)}")
        score -= 15
    else:
        issues.append(f"✅ 无违规引导词")
    
    # 6. 检查口语化程度（加强版）
    oral_words = ['啊', '呢', '吧', '嘛', '哈哈', '哎', '嘿', '哦', '呗', '啧', '得嘞', '甭']
    oral_count = sum(1 for w in oral_words if w in content)
    if oral_count >= 2:
        issues.append(f"✅ 口语化自然")
        score += 3
    elif oral_count >= 1:
        issues.append(f"✅ 有口语化")
    else:
        issues.append(f"⚠️  建议更口语化，加个语气词")
        score -= 5
    
    # 7. 第一人称即时感检查（"今天/今早/昨晚/刚"开头）
    if content.startswith(('今天', '今早', '昨晚', '刚', '刚刚', '昨天下班', '前两天')):
        issues.append(f"✅ 第一人称即时场景开头")
        score += 3
    else:
        issues.append(f"⚠️  非即时场景开头，建议加'今天'等时间锚点")
        score -= 3
    
    return max(score, 0), issues

def generate_openings(topic_key, count=5):
    """生成多种爆款开头供选择"""
    openings = {
        'salary': [
            '今天发工资，到账14200。',
            '发工资第3天，余额还剩3200。',
            '今天算了算账，这个月花了7000。',
            '工资到手14200，交完房租就剩一半了。',
            '今天看了看银行卡余额，愣了半天。',
        ],
        'relative': [
            '今天大姑打电话说她孙子要来北京玩。',
            '今天家庭聚会，二姨问我在北京挣多少钱。',
            '今天接到发小电话，说想找我帮忙。',
            '今天远房表哥来北京了，说让我安排接待。',
            '今天亲戚群里有人@我，说有事找我。',
        ],
        'age35': [
            '今天公司裁员，名单里有我。',
            '今天公司来了个新同事，98年的。',
            '今天拿了体检报告，三项异常。',
            '今天投了20份简历，一个回音都没有。',
            '今天开会，领导说年轻人要多加班。',
        ],
        'takeout': [
            '加班点外卖，备注写不要香菜。',
            '今天外卖迟到了40分钟。',
            '今天外卖撒了一半，汤流了一袋子。',
            '今天点外卖，商家把备注看成了反的。',
            '今天下雨天，外卖小哥满头大汗站在门口。',
        ]
    }
    
    return openings.get(topic_key, openings['salary'])[:count]

def pre_publish_check(content_id):
    """发布前一键检查"""
    # 从内容库读取内容
    content_dir = os.path.join(BASE_PATH, "references")
    filepath = None
    
    for f in os.listdir(content_dir):
        if f.endswith('.json'):
            try:
                with open(os.path.join(content_dir, f), 'r', encoding='utf-8') as fp:
                    c = json.load(fp)
                if c.get('id') == content_id:
                    filepath = os.path.join(content_dir, f)
                    break
            except:
                pass
    
    if not filepath:
        print(f"❌ 找不到内容: {content_id}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    content = data['content']
    
    print(f"{'='*60}")
    print(f"🔍 发布前质量检查 - {content_id}")
    print(f"{'='*60}")
    print(f"主题: {data.get('theme','')}")
    print()
    
    score, issues = check_content(content)
    
    for issue in issues:
        print(f"  {issue}")
    
    print()
    print(f"📊 质量得分: {score}/100")
    
    if score >= 90:
        print(f"🏆 质量等级: S级（爆款相！）")
        print(f"✅ 可以放心发布")
    elif score >= 75:
        print(f"🥇 质量等级: A级（优质内容）")
        print(f"✅ 可以发布")
    elif score >= 60:
        print(f"🥈 质量等级: B级（一般内容）")
        print(f"⚠️  建议优化后再发布")
    else:
        print(f"🥉 质量等级: C级（待改进）")
        print(f"❌ 建议重写")
    
    return score

def main():
    if len(sys.argv) < 2:
        print("用法: python quality_checker.py <command>")
        print()
        print("命令:")
        print("  check <内容ID>       发布前质量检查")
        print("  openings <主题>      生成爆款开头供选择")
        print("  text <内容文本>      检查任意文本")
        print()
        print("示例:")
        print("  python quality_checker.py check P01_d45_n1")
        print("  python quality_checker.py openings salary")
        return
    
    command = sys.argv[1]
    
    if command == 'check':
        content_id = sys.argv[2]
        pre_publish_check(content_id)
    
    elif command == 'openings':
        topic = sys.argv[2] if len(sys.argv) > 2 else 'salary'
        openings = generate_openings(topic)
        print(f"✨ 爆款开头模板（{topic}主题）:")
        print()
        for i, o in enumerate(openings, 1):
            print(f"{i}. {o}")
    
    elif command == 'text':
        text = sys.argv[2]
        score, issues = check_content(text)
        print(f"📊 质量得分: {score}/100")
        for issue in issues:
            print(f"  {issue}")
    
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == '__main__':
    main()
