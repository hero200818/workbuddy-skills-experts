#!/usr/bin/env python3
"""
AI内容生成器 v3.0 - 根据爆款特征自动生成新内容
基于已验证的爆款公式v3.0（冲突-发展-留白三段式），自动生成符合老周人设的微头条
"""
import json
import os
import sys
import random
import re
from datetime import datetime

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 爆款公式v3.0三段式模板库
TEMPLATES = {
    'salary': {
        'name': '工资/收入主题（已验证97.8万展现爆款）',
        'conflicts': [
            '今天发工资，到账{salary}。我先转了{rent}房租，再转{family}给家里，又留了{expense}吃饭，还完信用卡，余额就剩{balance}了。',
            '发工资第{day}天，看了看余额，还剩{balance}。旁边同事点了杯{coffee}的奶茶，我默默喝了口自己带的白开水。',
            '今天算了算账，这个月花了{expense}，工资就剩{balance}了。坐在工位上，我盯着记账软件发了半天呆。',
            '工资到手{salary}，交完房租{rent}，给家里{family}，女朋友生日又花了{expense}。剩下{balance}，我看着余额，手心有点凉。',
            '今天同事问我的工资够不够花，我说够花，就是别生病。他愣了一下，说这话听着怎么像句遗言。我说，在北京待久了都这样。',
            '工资到账那天，我先还了花呗，又还了信用卡，再看余额，就剩{balance}。突然觉得，这个月工资好像没来过。',
            '今天看到一个帖子，说月薪过万的人是什么体验。我想了想，我14200，体验就是：房租3800、给家里2000、吃饭2000，剩下全是数字游戏。',
            '发工资前三天，我给自己立了个规矩：这周不点外卖。结果今天加班到9点，点了。不是不自律，是加班费不够外卖钱。'
        ],
        'developments': [
            '35岁了，工资从5千涨到{salary}，存款还是没多少。不是不想存，是真存不下来。',
            '同事问我发工资了要不要一起吃顿好的，我说算了，回去吃泡面。他笑我抠，我没说话。',
            '这个月还得吃饭通勤，我算了算，一天最多花50，不然月底肯定透支。',
            '我在北京10年，工资从3千涨到{salary}，可房租从800涨到{rent}，物价翻了一倍，存款还是那点。',
            '我跟小林说这个月又没存下钱，她说正常，北京的钱就是过路财神，看一眼就得走。我笑了，笑完心里有点酸。',
            '我算了算，如果每个月能多存500，一年也就6000。在北京，6000连一平米都买不起。这么一想，又释然了。'
        ],
        'endings': [
            '你们发工资第几天开始吃土？',
            '你们一个月能存下多少钱？',
            '不是我抠，是真没办法。你们呢？',
            '你们说，这日子怎么就过成了这样？',
            '你们工资到账后，是先还债还是先存钱？',
            '有没有跟我一样，工资到账的快乐，就持续了一分钟？'
        ],
        'variables': {
            'salary': ['14200'],
            'balance': ['2000', '2800', '1500', '3200'],
            'expense': ['2000', '3000', '2500', '3500'],
            'rent': ['3800'],
            'family': ['2000'],
            'credit': ['2500', '2000', '3000', '2200'],
            'day': ['3', '5', '7', '10'],
            'coffee': ['30', '25', '35', '28']
        }
    },

    'relative': {
        'name': '人情世故/亲戚主题（已验证19.9万展现爆款）',
        'conflicts': [
            '今天{relative}打电话说{event}，让我{request}。我说我就是个打工的，真没那个能力。',
            '今天家庭聚会，{relative}问我{question}。我笑了笑，说还行，转头把话岔开了。',
            '今天{relative}找我帮忙，说{reason}。我硬着头皮答应了，挂了电话心里堵得慌。',
            '今天接到{relative}电话，说{news}。我说{relative}，我一个月就那么点工资，真帮不上。'
        ],
        'developments': [
            '{relative}沉默了一会儿，说你这孩子怎么这么不懂事。我喉咙发紧，半天没说出话来。',
            '在北京我是白领，在家里我是混得好的。可谁知道我连自己都快养不活了。',
            '我想起去年过年，{relative}在饭桌上说我混得好，让弟弟妹妹都跟我学。我低着头没敢接话。',
            '不是不想帮，是我自己都还欠着花呗。这话我从来没跟家里说过。'
        ],
        'endings': [
            '你们遇到过这种亲戚吗？',
            '你们说我做得对吗？',
            '你们会怎么处理这种事？',
            '人情世故真的太难了。你们呢？'
        ],
        'variables': {
            'relative': ['大姑', '二姨', '远房表哥', '发小'],
            'event': ['她孙子要来北京玩', '家里缺钱', '想让我帮忙找工作', '要结婚随礼'],
            'request': ['接待一下吃住我安排', '转5000块钱', '帮忙找个工作', '随礼1000'],
            'question': ['在北京一个月挣多少钱', '什么时候买房', '什么时候结婚', '混得怎么样'],
            'reason': ['他儿子要结婚', '家里装修缺钱', '他想来北京玩', '他没工作了'],
            'news': ['家里缺钱', '她孙子要结婚', '想让我帮忙', '想我了']
        }
    },

    'age35': {
        'name': '35岁危机主题（全网最热+粉丝画像93.5%匹配）',
        'conflicts': [
            '今天公司裁员名单出来了，我在里面，但没走成。领导找我谈话，说你是老员工了，再给你一次机会。',
            '今天公司来了个新同事，98年的。他第一天就喊我周叔，我愣了一下，笑着应了。',
            '今天拿了体检报告，有三项异常。医生说少熬夜少喝酒多运动。我笑了笑没说话。',
            '今天投了20份简历，一个回音都没有。35岁，好像成了一个原罪。'
        ],
        'developments': [
            '新同事学东西快，加班到10点还精神抖擞。我坐在工位上，白头发又多了几根，偷偷拔了。',
            '晚上回到家，我算了算房贷车贷孩子学费，发现根本不敢辞职。不是不想走，是走不了。',
            '我翻了翻手机，通讯录里能说心里话的，一只手数得过来。都忙，都累。',
            '去年被优化的老赵，到现在还没找到工作。每次想到他，我心里就咯噔一下。'
        ],
        'endings': [
            '你们被裁过吗？最后怎么走的？',
            '你们是什么时候开始被叫叔叔/阿姨的？',
            '35岁，你们慌吗？',
            '你们体检报告怎么样？'
        ],
        'variables': {}
    },

    'takeout': {
        'name': '外卖/吃饭日常（已验证30.3%点击率爆款）',
        'conflicts': [
            '加班点外卖，备注写{note}。送来一看，{result}。',
            '今天外卖迟到了{minutes}分钟，骑手小哥进门的时候，手都在抖。',
            '今天外卖撒了一半，汤流了一袋子。骑手站在门口，满头大汗，说哥对不起我赔你。',
            '今天点外卖，商家把备注看反了：我写{note}，他给我放了{result}。'
        ],
        'developments': [
            '我打电话过去，商家说哦你家备注我看成{misread}了。我气笑了，又觉得没力气吵。',
            '我看着他那样，突然想起去年冬天自己送文件迟到被骂的样子。心一下就软了。',
            '本来想给差评，看他那样又不忍心了。大家都不容易。',
            '我把袋子拎进办公室，汤还在往外渗。同事问我怎么了，我说没事，就是手滑了。'
        ],
        'endings': [
            '你们遇到过这种事吗？',
            '你会给迟到的外卖差评吗？',
            '不是我大方，是我也有过难的时候。你们呢？',
            '大家都不容易啊。你们呢？'
        ],
        'variables': {
            'note': ['不要香菜多放辣', '不要葱多放醋', '不要辣多放蒜'],
            'result': ['香菜堆成山，辣度为零', '葱放了一堆，醋只有一点', '一点不辣，蒜味冲天'],
            'misread': ['多放香菜不要辣', '多放葱不要醋', '多放蒜不要辣'],
            'minutes': ['40', '30', '50', '25']
        }
    },

    'family': {
        'name': '家庭/亲情主题（粉丝画像75分匹配）',
        'conflicts': [
            '我妈今天打电话，说最近老梦见我小时候。说着一半，她停住了，说没事没事，你忙吧。',
            '今天给家里转{family}，我爸在电话里说，你自己够花吗？我说够，其实工资到手只剩{balance}了。',
            '国庆回家，我妈提前三天就开始买菜。我走的时候，她往我包里塞了两盒牛奶。',
            '昨晚翻到去年过年回家拍的视频，我妈在厨房忙活，背影看着又矮了一些。'
        ],
        'developments': [
            '挂了电话，我坐在出租屋里，半天没动。30多岁的男人，眼泪不知道怎么就下来了。',
            '不是不想回去，是回去一趟来回车票{expense}，还得给家里留点。',
            '我爸一辈子没说过"想我"，但每次我回家，他都提前把房间收拾得干干净净。',
            '我在北京10年，陪他们的时间加起来不到一年。'
        ],
        'endings': [
            '你们多久给爸妈打一次电话？',
            '你们有多久没回家了？',
            '这句话，你们能听懂吗？',
            '你们爸妈，也这样吗？'
        ],
        'variables': {
            'family': ['2000', '2000', '2000', '2000'],
            'balance': ['2000', '1500', '2800', '1800'],
            'expense': ['1200', '800', '1500', '1000']
        }
    },

    'humor': {
        'name': '轻松幽默+反转+温度主题（周三重点发力日）',
        'conflicts': [
            '今天公司来了个新人，管我叫周叔。我说叫周哥就行，他说好的周叔。我笑了笑，行吧，周叔就周叔。',
            '今天开会，领导说年轻人要多加班，是机会。我笑了笑没接话。散会后95后同事问我怎么不说话，我说我35了，机会留给你们。',
            '今天外卖备注多放香菜，商家给做了多放辣。我吃了两口，辣得直喝水，还是吃完了——退回去太麻烦了，而且真饿了。',
            '今天地铁上给大爷让座，大爷说不用不用，你坐，我上班站了一天了。我愣住——大爷工牌上的公司，跟我一个写字楼。',
            '今天同事问我怎么天天带饭，我说省钱。他笑我一个月省不了几块钱。我说省下来的钱，刚好够还花呗。',
            '今天点外卖，备注写了不要辣多放蒜。送来一看，一点不辣，蒜味冲天。我拎着袋子进办公室，汤还在往外渗。',
            '今天女朋友小林说我胖了，我上秤一看，比去年重了8斤。我说都是加班的功劳，她说你加班是长肉还是长钱？',
            '今天去超市，收银员扫完说一共82块5。我掏出一叠优惠券，她说你这券都过期了。我愣了，过期半年了，我一直当宝贝攒着。',
            '今天开会领导画饼，说年底给大家涨薪20%。散会回工位，隔壁工位的小王说：去年也是这么说的，涨了，从8%涨到9%。我听完差点把可乐喷出来。',
            '今天部门团建，说要搞个"信任背摔"。我排在最后一个，前面几个95后摔完都有人接。到我的时候，后面人一哄而散，说周叔太重了接不住。我在地上躺了五秒，自己爬起来了。',
            '今天办公室新来的小姑娘问我：叔，你平时用什么护肤品？我说大宝。她愣了一下，说：叔，你是真养生还是真省钱？我说都占点。',
            '今天点了个外卖，备注写"少油少盐谢谢老板"。送到一看，油汪汪的。我打电话问，老板说：少油少盐是给减肥的人吃的，你这单我看你头像挺胖的，就正常做了。我盯着头像看了半天，那是我家猫。',
            '今天跟小林逛街，她试了件899的外套，问我好看吗。我说好看，她放下说：算了，太贵了。我说买吧，你穿真好看。她说：周哥你今天不对劲，你是不是藏私房钱了？我赶紧说：没有，就是觉得好看。',
            '今天坐地铁，一个大哥手机外放刷短视频，声音巨大。我忍了一路，快下车时他问我：哥们，你忍了一路了吧？我点头。他说：我也是，我耳机坏了，故意外放，就想看看谁能忍过我。我愣在原地，他先下车了。',
            '今天公司体检，医生看着我的报告说：你这身体比实际年龄老五岁。我说是不是熬夜多了？他说：不是，是压力大，体检单上都写着你天天加班。我一看，单子上真的写着"工作压力大"——原来体检单是AI写的。',
            '今天同事生日，我们凑钱买了个蛋糕。分蛋糕时，95后小妹说：周叔，你多吃点，你这个年纪新陈代谢慢了。我说：谢谢，你这话听着像关心，又像扎心。'
        ],
        'developments': [
            '同事说你怎么脾气这么好，我说不是脾气好，是懒得计较，计较也计较不出钱来。',
            '回到工位，我喝了口水，突然觉得这事能笑一天。生活就这样，苦中作乐呗。',
            '晚上回去跟小林说，她笑得不行，说我这是把倒霉过成了段子。',
            '我本来想生气，转念一想，气也没用，还伤身体。35岁了，学会了自己哄自己。',
            '我愣了两秒，然后没忍住笑了。成年人的崩溃，有时候就是这么滑稽。',
            '我看了看自己的工牌，又看了看他，最后谁也没说话，一起等电梯。成年人的体面，就是装作没听见。',
            '小林说，你这种人就适合在互联网，因为你们永远在"反转"。我说这词儿我都听不懂，她就笑。',
            '我想了想，好像确实是我错了。但错哪了，我到现在也没想明白。'
        ],
        'endings': [
            '你们遇到过这种哭笑不得的事吗？',
            '你们说，这算不算成年人的体面？',
            '你们有没有什么沙雕日常，说来听听？',
            '这种日子，笑着过总比哭着过强，你们说是吧？',
            '你们身边有没有这种"冤种"时刻？',
            '你们猜，这种时候是笑还是不笑？',
            '说出来你们可能不信，我居然习惯了。你们呢？',
            '你们公司，有没有这种神人？'
        ],
        'variables': {
            'family': ['2000', '2000', '2000', '2000']
        }
    }
}


def fill_template(template_str, variables, pair_idx=None):
    """填充模板变量（支持含/的复合变量名 + #N索引配对 {场景#0}）
    pair_idx: 所有#N变量使用该下标（保证同组配对）"""
    def replace_var(match):
        var_name = match.group(1)
        # 支持 {变量#N} 索引形式：三个变量用同一下标配对（如 表面好事#0 真实落差#0）
        if '#' in var_name:
            base, idx = var_name.split('#', 1)
            try:
                idx = int(idx)
            except ValueError:
                idx = None
            if base in variables and isinstance(variables[base], list):
                if idx is not None and len(variables[base]) > idx:
                    # 若传入配对下标，强制使用配对下标对应的元素
                    if pair_idx is not None and pair_idx < len(variables[base]):
                        return variables[base][pair_idx]
                    return variables[base][idx]
                return random.choice(variables[base])
            return match.group(0)
        if var_name in variables:
            return random.choice(variables[var_name])
        return match.group(0)
    return re.sub(r'\{([^}]+)\}', replace_var, template_str)


def generate_one(theme_key):
    """生成一条内容（三段式：冲突-发展-留白）"""
    theme = TEMPLATES.get(theme_key)
    if not theme:
        print(f"❌ 未知主题: {theme_key}")
        return None

    conflict = fill_template(random.choice(theme['conflicts']), theme['variables'])

    # 发展段双句拼接，增加细节和字数（110-140字黄金区间）
    dev_pool = list(theme['developments'])
    random.shuffle(dev_pool)
    development = fill_template(dev_pool[0], theme['variables'])
    for extra in dev_pool[1:]:
        extra_filled = fill_template(extra, theme['variables'])
        if extra_filled != development and len(conflict) + len(development) + len(extra_filled) + 20 < 150:
            development = development + extra_filled
            break

    ending = fill_template(random.choice(theme['endings']), theme['variables'])

    content = f"{conflict}{development}{ending}"

    return {
        'theme_key': theme_key,
        'theme_name': theme['name'],
        'content': content,
        'content_length': len(content)
    }


def generate_batch(theme_key, count=5):
    """批量生成多条内容"""
    print(f"🤖 批量生成内容 - 主题: {TEMPLATES[theme_key]['name']}")
    print(f"生成数量: {count}条")
    print()

    results = []
    for i in range(count):
        result = generate_one(theme_key)
        if result:
            results.append(result)
            print(f"{i+1}. 【{result['content_length']}字】")
            print(f"   {result['content']}")
            print()

    return results


def save_to_library(results):
    """保存到内容库（自动查重：开头25字相同视为重复，自动重新生成）"""
    content_dir = os.path.join(BASE_PATH, "references")

    # 找最大的day编号
    existing_days = []
    if os.path.exists(content_dir):
        for f in os.listdir(content_dir):
            if f.startswith('day') and f.endswith('.json'):
                try:
                    day = int(f.split('_')[0][3:])
                    existing_days.append(day)
                except:
                    pass

    next_day = max(existing_days) + 1 if existing_days else 1

    # 加载已有内容开头（前25字），用于查重
    existing_prefixes = set()
    if os.path.exists(content_dir):
        for f in os.listdir(content_dir):
            if f.startswith('day') and f.endswith('.json'):
                try:
                    d = json.load(open(os.path.join(content_dir, f), encoding='utf-8'))
                    existing_prefixes.add(d.get('content', '')[:25])
                except:
                    pass

    saved = 0
    for i, result in enumerate(results, 1):
        filename = f"day{next_day:02d}_num{i}.json"
        filepath = os.path.join(content_dir, filename)

        data = {
            'id': f'P01_d{next_day}_n{i}',
            'day': next_day,
            'number': i,
            'title': result['theme_name'][:20],
            'theme': result['theme_name'],
            'hook_type': '评论钩子',
            'image_suggestion': '暖色调氛围感图片',
            'content': result['content'],
            'content_length': result['content_length'],
            'status': 'pending',
            'deep_version_version': '3.0',
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'auto_generated': True,
            'structure': '冲突-发展-留白三段式'
        }

        # 查重：开头25字相同则跳过（视为重复内容）
        prefix = data['content'][:25]
        if prefix in existing_prefixes:
            print(f"⚠️ 检测到重复内容（开头相同），跳过: {data['content'][:35]}...")
            continue
        existing_prefixes.add(prefix)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        saved += 1
        print(f"✅ 已保存: {data['id']}")

    print(f"\n共保存 {saved} 条新内容到内容库")


def generate_from_gene(gene_key, count=3):
    """用爆款基因库模板生成内容（已验证爆款结构复用）"""
    # 基因型映射
    GENE_MAP = {
        'salary': '发工资算账型',
        'takeout': '外卖共情型',
        'relative': '亲戚求助型',
        'national': '国庆账单型',
        'workplace': '职场对比型',
        'family': '家庭细节型',
        'contrast': '情绪反差型',
    }
    gene_name = GENE_MAP.get(gene_key)
    if not gene_name:
        print(f"❌ 未知基因型: {gene_key}（可用: salary/takeout/relative/national/workplace/family/contrast）")
        return None

    try:
        genes = json.load(open(os.path.join(BASE_PATH, "references/viral_genes.json"), encoding="utf-8"))
    except Exception as e:
        print(f"❌ 基因库读取失败: {e}")
        return None

    gene = next((g for g in genes["top_performers"] if g["name"] == gene_name), None)
    if not gene:
        print(f"❌ 基因库中未找到: {gene_name}")
        return None

    # 基因变量池（人设数字锁定）
    GENE_VARS = {
        'salary': {'吃饭钱': ['2500', '3000', '2000'], '余额': ['1800', '2200', '1500'],
                   '生理反应': ['叹了口气', '手心有点凉', '心里堵得慌'],
                   '感慨': ['这日子怎么就过成了这样', '钱是真不经花', '一年到头还是没攒下'],
                   '钩子': ['你们发工资第一件事干啥？', '你们一个月能存下多少钱？', '你们算过自己还剩多少吗？']},
        'takeout': {'问题': ['迟到了40分钟', '撒了一半，汤流了一袋子', '备注看反了，香菜堆成山'],
                    '骑手动作': ['进门的时候手都在抖', '站在门口满头大汗', '连声说哥对不起'],
                    '生理反应': ['心一下就软了', '喉咙有点堵', '鼻子有点酸'],
                    '差评/投诉': ['给差评', '投诉', '发火'],
                    '回忆/共情': ['我看着他那样，想起去年冬天自己送文件迟到被骂的样子', '他满头汗，我气一下就消了', '都是讨生活的人，谁也不容易'],
                    '感悟': ['对别人宽容', '大家都不容易', '体谅别人'],
                    '钩子': ['你们给过迟到的外卖好评吗？', '你们遇到过这种事吗？', '你们会投诉吗？']},
        'relative': {'亲戚': ['大姑', '二姨', '远房表哥'], '要求': ['借5000块钱周转', '帮忙找个工作', '随礼1000'],
                     '拒绝理由': ['我就一打工的', '我工资就那么点', '我自己都欠着花呗'],
                     '亲戚反应': ['沉默了一会儿，说你咋这么不懂事', '挂电话前叹了口气', '说你这孩子真抠'],
                     '生理反应': ['喉咙发紧', '心里堵得慌', '手心有点凉'],
                     '人设': ['白领', '程序员', '混得好的'],
                     '家里人设': ['混得最好的那个', '全家的指望', '亲戚眼里的能人'],
                     '真实困境': ['房租都还没着落', '信用卡还没还清', '自己都快养不活了'],
                     '钩子': ['你们遇到过这种亲戚吗？', '你们说我做得对吗？', '你们会怎么处理？']},
        'national': {'花账': ['车票800，随礼3000，吃饭1500', '来回车票800，请客600，随礼3000', '车票800，礼物1000，聚会1200'],
                     '大件': ['给爸妈买了个按摩仪900', '换了个手机3000', '给小林买了条项链1500'],
                     '总数': ['6500', '5800', '7200'], '场景': ['沙县小吃', '黄焖鸡米饭', '兰州拉面'],
                     '食物': ['拌面', '鸡腿饭', '牛肉面'],
                     '钩子': ['你们国庆回来，余额还够看吗？', '你们国庆花了多少？', '国庆账单你们敢算吗？']},
        # 职场对比型（对比写法：人家vs自己）
        'workplace': {'同事事件': ['组里来了个应届生，张口就要18000，领导居然批了', '95后同事又双叒加薪了，我三年没动过', '新来的00后说35岁就该被优化，我正好听见'],
                      '自己的反应': ['默默打开手机看了下余额，又默默关上', '把手里的可乐捏得咯吱响', '笑了笑没接话，回工位改了一下午bug'],
                      '同一件事': ['都是写代码的', '都是天天加班的', '都在这个行业里'],
                      '人家的好': ['人家入职就是18000', '人家一年调两次薪', '人家还年轻，有的是机会'],
                      '自己的惨': ['我干了10年才14200', '我3年没涨过一分钱', '我35岁连跳槽的勇气都快没了'],
                      '生理反应': ['喉咙有点发紧', '心里堵得慌', '手心有点凉'],
                      '感慨': ['能力没跟上年纪，才是最扎心的', '年轻真好，试错成本低', '这行就是这么现实']},
        # 家庭细节型（具体物件细节拉满）
        'family': {'场景': ['今天我妈把我攒了半个月工资买的衬衫当抹布擦了桌子，擦完还说：这布料吸水，当抹布真合适。',
                           '今天我爸翻出我小时候的照片，一张张看，边看边说：这日子过得太快了，你小时候还骑我脖子上赶集。',
                           '今天女朋友小林把我妈留给我的老照片一张张翻出来看，看完说：你妈当年真好看，比我好看。',
                           '今天我妈给我留了一碗热了三遍的排骨汤，汤面上浮着一层油，她舍不得倒，说不吃浪费。',
                           '今天我爸在电话里咳嗽了两声，我问怎么了，他说没事，就是有点想你妈做的饭了。',
                           '今天小林加班到十点，回来路上给我带了个烤红薯，说天冷了，捧着暖和。'],
                   '反应': ['愣在原地半天没说话', '眼眶一下就热了', '鼻子一酸，赶紧转身去倒水', '笑着笑着就不说话了', '喉咙堵得说不出话'],
                   '生理反应': ['喉咙堵得慌', '心里酸酸的', '眼睛发涩', '手心有点凉'],
                   '钩子': ['你们多久没回家了？', '你们爸妈，也这样吗？', '你们有多久没吃到家里的热饭了？', '你们多久没给家里打过电话了？']},
        # 情绪反差型（表面好事→真实落差→自我调侃）
        'contrast': {'表面好事': ['发了个季度奖，6000块，同事都恭喜我', '领导夸我能干，说要给我涨薪', '相亲对象说我这人实在，可以考虑'],
                     '真实落差': ['奖金要扣税，到手4800，还不够还信用卡', '涨薪是涨了，从14000涨到14200', '实在的意思是我工资实在不高，她说考虑考虑'],
                     '细节暴露': ['我算了一下，扣完房租和家里的，又回到解放前', '算下来一个月就多200，一顿饭钱', '我请她吃了碗沙县，她说我挺会过日子'],
                     '生理反应': ['笑着笑着就沉默了', '心里咯噔一下', '嘴上说谢谢，心里凉了半截'],
                     '自我调侃': ['成年人的快乐，就是保质期短了点', '穷不可怕，可怕的是穷得这么稳定', '不怪别人，怪我自己太会过日子']},
    }
    # 变量池优先级：基因库自带variables > 内置GENE_VARS > 空
    vars_pool = dict(gene.get('variables', {}) or {})
    builtin_vars = GENE_VARS.get(gene_key, {})
    for k, v in builtin_vars.items():
        if k not in vars_pool:
            vars_pool[k] = v
    # 兼容旧模板的{钩子}变量（新钩子分类体系由下方钩子增强逻辑处理）
    vars_pool.setdefault('钩子', ['你们说呢？'])

    print(f"🧬 爆款基因生成 - {gene['name']}（已验证: {gene['proven_data'][:50]}）")
    print(f"生成数量: {count}条\n")

    results = []
    for i in range(count):
        template = gene['template']
        # 开头变体：随机使用一个开头变体（若基因库配置了）
        opening_variants = gene.get('opening_variants', [])
        if opening_variants:
            variant = random.choice(opening_variants)
            # 取模板原文开头到第一个"。"作为原开头，替换为变体
            first_period = template.find('。')
            if first_period > 0:
                template = variant + template[first_period+1:]
        # 随机配对下标：让模板中所有 #N 用同一个随机下标（如 #0 全部随机取同一组）
        pair_idx = random.choice(range(3))
        # 填充分段变量（配对下标作用于 #N 变量）
        filled = fill_template(template, vars_pool, pair_idx=pair_idx)
        # 钩子增强：优先用模板自带钩子，否则从基因库5大钩子分类随机抽取
        if '{钩子}' in filled:
            # 从5大钩子分类中随机选一个分类，再从分类中随机选钩子
            hook_cats = [h for h in genes.get('hook_library', []) if isinstance(h, dict) and 'hooks' in h]
            if hook_cats:
                cat = random.choice(hook_cats)
                filled = filled.replace('{钩子}', random.choice(cat['hooks']))
            else:
                filled = filled.replace('{钩子}', random.choice(genes['hook_library']))
        elif not filled.rstrip().endswith('？') and not filled.rstrip().endswith('吗'):
            # 内容没有自带钩子时，追加一个5大钩子分类的评论钩子（提升评论率）
            hook_cats = [h for h in genes.get('hook_library', []) if isinstance(h, dict) and 'hooks' in h]
            if hook_cats:
                cat = random.choice(hook_cats)
                filled = filled.rstrip('。') + '。' + random.choice(cat['hooks'])
        # 兜底清理残余占位符
        filled = re.sub(r'\{[^}]*\}', '', filled).strip()
        # 去除多余标点
        filled = filled.replace('，。', '。').replace('。。', '。')
        if filled.endswith('。？'):
            filled = filled[:-2] + '？'

        results.append({
            'theme_key': gene_key,
            'theme_name': gene['name'],
            'content': filled,
            'content_length': len(filled)
        })
        print(f"{i+1}. 【{len(filled)}字】")
        print(f"   {filled}\n")

    save_to_library(results)
    return results


def main():
    if len(sys.argv) < 2:
        print("用法: python content_generator.py <command>")
        print()
        print("命令:")
        print("  themes                    列出所有主题模板")
        print("  generate <主题> <数量>    生成内容并预览")
        print("  save <主题> <数量>        生成内容并保存到内容库")
        print("  rebalance                 按爆款主题配比自动生成补充内容")
        print("  gene <基因型> <数量>      用爆款基因库模板生成（发工资/外卖/亲戚/国庆）")
        print()
        print("示例:")
        print("  python content_generator.py themes")
        print("  python content_generator.py generate salary 5")
        print("  python content_generator.py save age35 3")
        print("  python content_generator.py rebalance")
        print("  python content_generator.py gene salary 3")
        return

    command = sys.argv[1]

    if command == 'themes':
        print(f"📂 可用主题模板:")
        for key, theme in TEMPLATES.items():
            print(f"  {key:<10} - {theme['name']}")

    elif command == 'generate':
        theme_key = sys.argv[2] if len(sys.argv) > 2 else 'salary'
        count = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        generate_batch(theme_key, count)

    elif command == 'save':
        theme_key = sys.argv[2] if len(sys.argv) > 2 else 'salary'
        count = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        results = generate_batch(theme_key, count)
        save_to_library(results)

    elif command == 'rebalance':
        # 按爆款主题配比生成补充内容：工资/人情世故/35岁/外卖/家庭 = 3:3:2:1:1
        plan = [('salary', 3), ('relative', 3), ('age35', 2), ('takeout', 1), ('family', 1)]
        all_results = []
        for theme_key, count in plan:
            results = generate_batch(theme_key, count)
            all_results.extend(results)
        save_to_library(all_results)
        print(f"\n🎯 主题配比优化完成：共生成 {len(all_results)} 条")

    elif command == 'gene':
        gene_key = sys.argv[2] if len(sys.argv) > 2 else 'salary'
        count = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        generate_from_gene(gene_key, count)

    else:
        print(f"❌ 未知命令: {command}")


if __name__ == '__main__':
    main()
