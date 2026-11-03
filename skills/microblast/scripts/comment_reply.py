#!/usr/bin/env python3
"""
评论回复生成器 v3.0 - 根据评论内容自动生成回复建议
基于 comment_templates.json v3.0（13种评论类型）
支持：reply, analyze
"""
import json
import os
import sys
import re
import random

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_FILE = os.path.join(BASE_PATH, "references", "comment_templates.json")

def load_templates():
    """加载评论话术库"""
    with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def classify_comment(comment_text, theme=None):
    """v3.0 自动判断评论类型（13种）"""
    text = comment_text.lower()
    original = comment_text
    
    # 粉丝专属（先判断，粉丝优先）
    if '粉丝' in original:
        return 'fan_special'
    
    # 质疑/抬杠型（"段子吗""编的""假的"等质疑真实性）
    doubt_keywords = ['假的', '编的', '不可能', '不信', '炒作', '噱头', '真的假的', '瞎编', '打草稿', '随口编', '编瞎话', '段子', '小说', '故事会']
    if any(k in text for k in doubt_keywords):
        return 'doubt_type'
    
    # 抬杠阴阳型（带刺但不直接质疑真实性）
    sarcastic_keywords = ['有钱你就', '没人挡', '有本事', '就这', '就这点', '抠门', '小气', '真行', '呵呵', '不算高', '也不高', '这还叫', '就这水平', '这点钱', '有啥用']
    if any(k in text for k in sarcastic_keywords):
        return 'sarcastic_type'
    
    # 苦情对比型
    bitter_keywords = ['比我还', '我更惨', '我连', '都拿不出', '更别说', '我一个月才', '比我强', '起码你', '还有工资']
    if any(k in text for k in bitter_keywords):
        return 'bitter_type'
    
    # 羡慕感叹型
    envy_keywords = ['工资好高', '好高', '真高', '羡慕', '混得好', '收入不错', '这么多', '一万多', '不错啊']
    if any(k in text for k in envy_keywords):
        return 'envy_type'
    
    # 好奇打探型
    curious_keywords = ['在哪', '哪里上班', '做什么', '啥工作', '工资多少', '多少工资', '房租多少', '哪个城市', '多少钱', '能存多少', '剩多少', '存多少', '包饭', '包吃', '管饭', '公司管']
    if any(k in text for k in curious_keywords):
        return 'curious_type'
    
    # 共鸣型
    resonance_keywords = ['我也是', '太真实了', '哭了', '说到我心里', '同款', '同感', '一样', '扎心', '真实', '心酸', '泪目', '完全不够', '太难了', '都一样', '感同身受']
    if any(k in text for k in resonance_keywords):
        return 'resonance_type'
    
    # 提问型
    question_keywords = ['怎么办', '怎么', '如何', '为什么', '吗？', '吗?', '？', '求', '建议', '方法', '咋办', '咋整']
    if any(k in text for k in question_keywords) and len(text) > 5:
        return 'question_type'
    
    # 神评论/搞笑
    funny_keywords = ['哈哈', '笑死', '逗', '人才', '有才', '梗', '哈哈哈', '笑喷']
    if any(k in text for k in funny_keywords):
        return 'god_type'
    
    # 安慰型
    comfort_keywords = ['加油', '抱抱', '不容易', '辛苦', '会好的', '坚持', '支持你', '保重', '注意身体']
    if any(k in text for k in comfort_keywords):
        return 'comfort_type'
    
    # 批评型
    criticism_keywords = ['不对', '错了', '不该', '不应该', '傻', '怂', '懦弱', '太弱', '窝囊', '看的淡', '太淡', '无情', '冷漠']
    if any(k in text for k in criticism_keywords):
        return 'criticism_type'
    
    # 科普解释型（纠正事实/解释含义，如"1800K是18000元"）
    explain_keywords = ['的意思是', '是', '等于', '不是', '指', 'K是', '代表']
    if any(k in text for k in explain_keywords) and len(text) <= 20 and '我' not in original:
        return 'short_type'

    # 认同观点型（对方认同并延伸观点：如"长期帮同事带早餐，会让对方形成理所当然的依赖"）
    agree_keywords = ['会', '应该', '确实', '就是这样', '说得对', '对，', '有道理', '没错', '就是这样', '早晚', '迟早', '必然', '肯定']
    if any(k in text for k in agree_keywords) and len(text) > 12 and '？' not in text:
        return 'agree_type'

    # 故事型（有细节的评论）
    if len(text) > 20 and ('我' in original or '我们' in original or '当年' in original or '之前' in original):
        return 'story_type'
    
    # 短评论
    if len(text) <= 10:
        return 'short_type'
    
    # 默认故事型
    return 'story_type'

# 人设数字锚点（用于填充占位符）
PERSONA = {
    'salary': '14200', 'rent': '3800', 'family': '2000',
    'city': '北京', 'job': '程序员', 'age': '35',
}

def fill_reply_template(template, comment_text, theme=None):
    """智能填充回复模板中的占位符"""
    text = template
    
    # 动态观点关键词提取（评论原文核心词，回填 {观点关键词}，让回复针对本条评论）
    if '{观点关键词}' in text:
        # 优先取评论中的核心观点短语
        key_phrases = []
        for kw in ['帮同事带早餐', '带早餐', '带饭', '理所当然', '依赖', '习惯', '拒绝', '借钱', '亲戚',
                   '工资', '外卖', '加班', '领导', '同事', '房东', '房租', '信用卡', '花呗', '存款',
                   '北京', '北漂', '35岁', '对象', '相亲', '父母', '爸妈']:
            if kw in comment_text:
                key_phrases.append(kw)
        # 取第一个命中的关键词（最核心的）
        view = key_phrases[0] if key_phrases else '这事'
        text = text.replace('{观点关键词}', view)
    
    # 人设锚点
    text = text.replace('{salary}', PERSONA['salary'])
    text = text.replace('{rent}', PERSONA['rent'])
    text = text.replace('{family}', PERSONA['family'])
    text = text.replace('{城市}', PERSONA['city'])
    text = text.replace('{职业}', PERSONA['job'])
    
    # 通用补充
    text = text.replace('{补充细节}', '35岁了，钱真是一分掰两半花')
    text = text.replace('{补充一句相关的}', '35岁的打工人都不容易')
    text = text.replace('{补充共鸣点}', '同是天涯打工人')
    text = text.replace('{共情表达}', '我懂你那种感觉')
    text = text.replace('{反思}', '当时就是太冲动了')
    text = text.replace('{补充感受}', '有你这句话，心里踏实多了')
    text = text.replace('{我的做法}', '该省省该花花，但房租和家里那份从来不省')
    text = text.replace('{相关场景}', '北漂的出租屋里')
    text = text.replace('{接梗/点赞}', '这梗我接住了')
    text = text.replace('{接梗}', '这梗我接住了')
    text = text.replace('{补充自己的难处}', '北京这地方，房租水电一扣，真剩不下啥')
    text = text.replace('{幽默回应}', '哈哈谁不是呢')
    text = text.replace('{承认对方}', '你说得对')
    text = text.replace('{自嘲细节}', '程序员，头发都快掉没了')
    text = text.replace('{生活压力描述}', '扣完房租给完家里，真剩不下啥')
    text = text.replace('{谦虚回应}', '一万四在北京真不算高')
    text = text.replace('{安慰表达}', '日子是一点点熬出来的')
    text = text.replace('{回应感叹}', '哈哈别羡慕，都是辛苦钱')
    text = text.replace('{称呼}', '兄弟')
    text = text.replace('{回应评论}', '谢谢支持')
    text = text.replace('{自嘲回应}', '我这不是拉不下脸嘛，就爱当个老好人')
    text = text.replace('{梗点}', '沙县大酒店的名号')
    text = text.replace('{对应事物}', '当地物价')
    text = text.replace('{相关场景}', '北漂的出租屋里')
    text = text.replace('{真实情况}', '真没你想的那么好')
    text = text.replace('{回应评论}', '谢谢支持')
    text = text.replace('{形容词}', '曲折')
    text = text.replace('{追问细节}', '后来呢')
    text = text.replace('{细节}', '那段日子')
    text = text.replace('{建议}', '先别急着答应，给自己留个缓冲')
    text = text.replace('{我的选择}', '硬着头皮答应了一半')
    text = text.replace('{结果}', '后来人家也习惯了，我再想拒绝都难')
    text = text.replace('{城市区域}', '北五环外')
    text = text.replace('{生活压力描述}', '扣完房租给完家里，真剩不下啥')
    text = text.replace('{谦虚回应}', '一万四在北京真不算高')
    
    # 兜底清理残余占位符
    text = re.sub(r'\{[^}]*\}', '', text)
    text = re.sub(r'[，,。]\s*[，,。]', '。', text)
    text = text.replace('。。', '。').replace('，，', '，').strip()
    # 清理"嗨，。你说"这类开头残标点
    text = re.sub(r'^([嗨唉哈])\s*[，,。]\s*', r'\1，', text)
    return text

def generate_replies(comment_text, theme=None):
    """生成3个回复建议（v3.0 13类型 + 智能填充）"""
    templates = load_templates()
    
    comment_type = classify_comment(comment_text, theme)
    
    type_names = {
        'resonance_type': '共鸣型评论',
        'story_type': '故事型评论',
        'question_type': '提问型评论',
        'doubt_type': '质疑型评论',
        'god_type': '神评论/搞笑',
        'comfort_type': '安慰型评论',
        'criticism_type': '批评型评论',
        'short_type': '短评论',
        'curious_type': '好奇打探型',
        'bitter_type': '苦情对比型',
        'sarcastic_type': '抬杠阴阳型',
        'envy_type': '羡慕感叹型',
        'fan_special': '粉丝专属互动',
        'agree_type': '认同观点型',
    }
    
    print(f"💬 评论内容: {comment_text}")
    print(f"📋 判断类型: {type_names.get(comment_type, '未知')}")
    print()
    
    # 获取对应类型的回复模板
    type_data = templates['comment_type_intelligence'].get(comment_type, {})
    reply_templates = type_data.get('reply_templates', [])
    
    if not reply_templates:
        print("❌ 未找到对应类型的回复模板")
        return comment_type
    
    print(f"✨ 生成3个回复建议（推荐第1个）:")
    print()
    
    for i, t in enumerate(reply_templates[:3]):
        recommended = " ⭐推荐" if i == 0 else ""
        filled = fill_reply_template(t['template'], comment_text, theme)
        print(f"{i+1}. 【{t['style']}】{recommended}")
        print(f"   {filled}")
        print()
    
    # 主题专属建议
    if theme:
        theme_strategies = templates.get('theme_specific_reply_strategies', {})
        for theme_name, strategy_data in theme_strategies.items():
            if isinstance(strategy_data, dict) and 'keywords' in strategy_data:
                if any(k in theme for k in strategy_data['keywords']):
                    print(f"📌 主题专属建议（{theme_name}）:")
                    for reply in strategy_data.get('specific_replies', [])[:2]:
                        print(f"   - {reply}")
                    break
    
    # 运营提示
    follow_up = type_data.get('follow_up_tip', '')
    if follow_up:
        print(f"💡 运营提示: {follow_up}")
    
    return comment_type

def icebreak(theme=None):
    """生成零评论破冰引导评论（发布后2小时内若0评论，用老周人设自评打破零评论）"""
    d = load_templates()
    zb = d.get('zero_comment_break_ice', {})
    pool = zb.get('by_theme', {})
    theme = theme or ''
    # 主题匹配：按关键词精确匹配对应破冰话术
    theme_rules = [
        ('亲戚/人情世故', ['亲戚', '大姑', '人情世故', '借钱', '随礼']),
        ('工资', ['工资', '钱', '收入', '余额', '账单']),
        ('外卖', ['外卖', '吃饭', '吃', '沙县', '黄焖鸡']),
        ('职场', ['职场', '工作', '同事', '领导', '加班', '开会']),
        ('家庭/亲情', ['家庭', '亲情', '爸妈', '妈', '爸', '家']),
        ('幽默/日常', ['幽默', '反转', '日常', '搞笑']),
        ('情感/北漂', ['情感', '北漂', '北京', '孤独', '35', '扎心']),
    ]
    key = None
    for rule_key, keywords in theme_rules:
        if any(kw in theme for kw in keywords):
            key = rule_key
            break
    if not key:
        # 默认工资（最稳题材）
        key = '工资'
    candidates = pool.get(key, [])
    if not candidates:
        print("❌ 无可用破冰话术")
        return
    print(f"🧊 零评论破冰评论（{key}题材，发布后2小时内发1条）：")
    for i, c in enumerate(candidates, 1):
        print(f"\n  {i}. {c}")
    print(f"\n⏰ 时机：发布后2小时（20:00-22:00黄金互动期）内发1条；2小时后仍0评论再补第2条")
    print(f"⚠️ 原则：像真人补充细节，不喊'点赞收藏关注'；发完要回复所有响应者")

def main():
    if len(sys.argv) < 2:
        print("用法: python comment_reply.py <command>")
        print()
        print("命令:")
        print("  reply <评论内容> [主题]   生成3个回复建议")
        print("  icebreak [主题]           生成零评论破冰引导评论（发布后2h内0评论时用）")
        print()
        print("示例:")
        print("  python comment_reply.py reply '太真实了，我也是这样' 工资")
        print("  python comment_reply.py reply '在哪上班啊工资这么高' 工资")
        print("  python comment_reply.py reply '有钱你就带呗，没人挡' 外卖")
        print("  python comment_reply.py icebreak 工资")
        return
    
    command = sys.argv[1]
    
    if command == 'reply':
        if len(sys.argv) < 3:
            print("❌ 需要评论内容")
            return
        comment = sys.argv[2]
        theme = sys.argv[3] if len(sys.argv) > 3 else None
        generate_replies(comment, theme)
    elif command == 'icebreak':
        theme = sys.argv[2] if len(sys.argv) > 2 else None
        icebreak(theme)
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == '__main__':
    main()
