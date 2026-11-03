# 爆款工坊 BestsellerWorks

## 项目标识
- **中文名称**：爆款工坊
- **英文标识**：BestsellerWorks
- **技能目录**：`toutiao-bestseller-generator`
- **创建日期**：2026-08-19

## 项目定位
输入图书/电视剧/电影名称，一键批量生成符合头条号平台规则的爆款文章，支持自动转图片、Word格式，以及浏览器自动发布。

## 核心功能
1. **智能类型识别**：自动识别7大品类（历史/育儿/情感/科幻/经管/文学/通用）
2. **背景资料检索**：自动联网检索作品背景、人物、情节、评价
3. **智能选题规划**：按品类比例规划N篇选题，覆盖人物/情节/观点/背景/对比
4. **爆款标题生成**：10大爆款标题公式，每篇1主标题+2备选
5. **风格化写作**：7套品类风格模板，去AI味，生动鲜活
6. **质量自检**：50+项质量检查，不达标自动修改
7. **多格式输出**：Markdown + Word + 图片（iOS液态玻璃风格）
8. **本地自动化**：Python脚本一键生成到指定目录
9. **浏览器自动发布**：自动登录头条号，上传文章和图片

## 调用方式
在新对话中直接说：
- 「用爆款工坊生成《XXX》」
- 「爆款工坊，帮我写《XXX》的头条文章」
- 「用爆款工坊，10篇，《XXX》」

## 关联工具
- **MarkPic**：Markdown转图片工具（已升级，支持批量处理、作者署名、自定义封面）
- **toutiao_generator.py**：本地文章生成脚本
- **toutiao_publisher.py**：浏览器自动发布脚本

## 已完成实战
- 《大明王朝1566》50篇（约19万字）
- 《养育男孩》10篇（约4.4万字）
- 《围城》10篇（约3.6万字，含71张配图）

## 本机 WorkBuddy 部署与适配（重要）

本技能已部署在 WorkBuddy 用户级技能目录，无需 `toutiao_auto_tool` 原结构：

- **技能位置**：`~/.workbuddy/skills/toutiao-bestseller-generator/`（生成器）+ `~/.workbuddy/skills/markpic/`（配图）
- **Python 依赖隔离 venv**：`~/.workbuddy/binaries/python/envs/default`（已装 requests/pyyaml/python-docx/pillow/playwright/pypandoc）
- **图片生成已内置适配**：`toutiao_generator.py` 生成图片时会自动调用 `~/.workbuddy/bin/run_markpic.py`（该启动器自动注入 Chromium/pandoc 的 Windows 风格 PATH，并通过 UTF-8 JSON 传中文参数，规避 Git Bash 编码坑），无需手动配置 python3 或 PATH。
- **手动批量配图**：`~/.workbuddy/bin/run_markpic_batch.py ./articles/ --style ios`
- **发布器兼容两种结构**：`toutiao_publisher.py` 的 `--batch` 既支持 `01_xxx/01_xxx.md` 子文件夹结构，也支持 `01_xxx.md + 01_xxx_*.png` 扁平结构（AI 手动产出常用）。
- **公众号署名**：`config.yaml` 中 `generation.image_author` 默认 `读读书悦悦己`，自动作为封面署名。

## 工具链健康检查（推荐定期运行）

新增一键自检脚本，验证整条工具链是否接线正确（venv / Chromium / pandoc / 启动器 / 技能 / 脚本导入 / 真实出图冒烟），缺哪环一眼可见：

```bash
C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe \
  C:/Users/Administrator/.workbuddy/bin/check_toolchain.py
```

输出逐项 `[OK]/[FAIL]` 与总体结论；最后一项会**真实渲染一张测试图**，因此也能顺带确认配图全链路可用。当前本机运行结果为 12/12 全部通过。

## 已知边界（非缺陷，使用前须知）
- **生成正文需外部 LLM API**：`toutiao_generator.py` 调豆包/OpenAI，需在 `config.yaml` 填真实 API Key；本机未配置，故该脚本仅做可运行性/集成验证，未做真实联网生成。AI（agent）也可按 SKILL.md 九步工作流直接撰写正文（无需 API）。
- **浏览器发布需头条号登录态**：`toutiao_publisher.py` 首次须 `--login` 扫码保存 cookies（涉及你的头条账号，请自行操作或明确授权）；头条页面改版时需更新脚本内选择器。
- **iOS 封面多标签组**为模板固定文案，与个别品类不完全贴合，属已知小瑕疵，不影响出图。

## 开放平台发布（爆文制造局 · Viral Article Forge）

为在 WorkBuddy 开放平台（open.workbuddy.cn）上架，项目对外名称定为 **「爆文制造局」**（英文 Viral Article Forge，标识 `viral-article-forge`，分类 内容创作）。本地「爆款工坊」触发词保留兼容。

**发布包**：`dist/viral-article-forge.zip`（约 54KB，根目录 `viral-article-forge/`，两级目录），内容：

```
viral-article-forge/
├── SKILL.md                 # 平台规范 frontmatter（description/_zh/_en、version、author 齐全）
├── references/              # 5 份写作规范
└── scripts/                 # generator / publisher / config.example / READMEs / 内置 md2img.py
```

- **自包含配图**：包内内置 `scripts/md2img.py`（67KB，CSS 内嵌，仅依赖系统 pandoc+Chromium），`generator._find_md2img` 首选脚本同目录副本，装到他人机器也能出图（已实测 PASS）。
- **净化**：无本机路径、密钥、Cookie。
- **发布步骤**：open.workbuddy.cn/skill/publish → 上传 zip → 配置技能 → 确认信息 → 提交审核（zip ≤3MB）。
- **若报 category 枚举不认**：将 `category: 内容创作` 改为 `writing` 后重打包。
