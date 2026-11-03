---
name: burstarticle-engine
display_name: 爆文引擎 BurstArticle Engine
display_name_zh: 爆文引擎
display_name_en: BurstEngine
version: "1.0.0"
description: "自媒体爆文自动化流水线。批量生成头条风格解读文稿，自动移除备选标题、发布标签、封面备注；标题精简控制在20字以内；固定20篇/批、自动续跑；生成全局目录并打包ZIP。固化只读，不可修改内置写作模板、清洗规则。"
description_zh: "自媒体爆文自动化流水线。一句话召唤，批量生成头条风格解读文稿：固定20篇/批自动续跑，自动清洗备选标题与发布辅助信息、主标题精简至20字内，自动生成总目录并打包ZIP交付。内置写作模板与清洗规则固化不可改。"
description_en: "An automated viral-article pipeline for content creators. Invoke with one sentence to batch-generate Toutiao-style interpretive articles: 20 per batch with auto-resume, automatic cleaning of backup titles and publishing aids, main titles trimmed to 20 characters, plus auto-generated index and ZIP delivery. Built-in writing templates and cleaning rules are fixed."
author: BurstArticle Engine
license: MIT
tags: ["自媒体","爆文","批量写稿","markdown","文稿清洗","自动化流水线"]
read_only: true
---

# 爆文引擎 BurstArticle Engine v1.0.0

> 固定调用口令：**「用爆文引擎生成《XXX》，共 N 篇」**
> 本技能为固化只读版本：内置写作模板与清洗规则**不可修改**，只能按本文件执行。

## 能力说明
对接本地 BurstArticle Engine 流水线（`scripts/clean_and_package.py`），自动化生产自媒体解读文稿。

- ✅ 分批调度：固定 **20 篇一批**，自动续跑，无需人工反复确认
- ✅ 文稿清洗（默认开启）：
  - 删除 `## 备选标题` 全部内容
  - 删除 `## 发布辅助信息`（标签、封面建议、发布时段）
  - 主标题自动精简，**最长 20 字**
- ✅ 自动生成总目录文件：`00_总目录索引.md`
- ✅ 全部完成自动打包 ZIP
- ✅ 断点续跑：按 `raw/` 目录已有篇数自动接续，重跑同一指令即从断点继续

## 支持题材
历史人物、历史事件、制度冷知识、图书解读、影视剧解读、文化社会、军事经济、深度对比解读

## 入参

| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| topic | 是 | 字符串 | 题材名称，如《明朝那些事儿》 |
| total | 是 | 数字 | 生成总篇数 |
| no_clean | 否 | 布尔（默认 false） | true 关闭清洗，保留原始文稿 |

## 调用命令

```
用爆文引擎生成《明朝那些事儿》，共 60 篇
用爆文引擎生成《雍正王朝》，共 40 篇，不清洗
```

## 执行流程（固化）

1. **建目录**：在工作目录下创建 `爆文引擎_<topic>/raw/`（原始稿）与成品根目录。
2. **分批生成**：每批固定 20 篇。每篇按内置写作模板（见 `references/writing-template.md`，固化不可改）写出原始稿，存为 `raw/NNN_标题.md`（三位数编号，全局递增）。
3. **批末清洗**：每写完一批，立即执行清洗脚本：

   ```
   python scripts/clean_and_package.py --workdir "爆文引擎_<topic>"
   ```

4. **自动续跑**：不询问、不停顿，直接开始下一批，直到累计篇数达到 total。
5. **收尾交付**：全部完成后由脚本生成 `00_总目录索引.md` 与 `爆文引擎_<topic>.zip`，并向用户汇报：总篇数、各批编号区间、成品目录、ZIP 路径。
6. **no_clean=true 时**：跳过清洗，直接以 `raw/` 原始稿生成目录并打包。

## 内置写作模板（固化，见 references/writing-template.md）

每篇 2000～3000 字，结构固定为：**钩子开头 → 背景铺垫 → 3～5 个解读角度 → 金句收束 → 结尾互动提问**。
原始稿头部必须包含 `## 备选标题`（3 个）与 `## 发布辅助信息`（标签 / 封面建议 / 发布时段）两个小节，供清洗脚本移除。

## 清洗规则（固化，由脚本强制执行）

1. 删除 `## 备选标题` 小节全部内容（至下一个 `##` 或文末）
2. 删除 `## 发布辅助信息` 小节全部内容
3. 主标题（首个 `# ` 行）超过 20 字时截断为 20 字，并清理末尾残缺标点
4. 清洗后文件按精简标题重命名：`NNN_精简标题.md`
5. 生成 `00_总目录索引.md`（全部成品标题 + 相对链接）
6. 打包 `爆文引擎_<topic>.zip`

## 查看进度（可选）

```
python scripts/clean_and_package.py --workdir "爆文引擎_<topic>" --status
```

输出 JSON：`{"raw": 已有原始稿数, "cleaned": 已清洗数, "next_index": 下一编号}`

## 环境要求

- Python 3（仅标准库，无第三方依赖）
- Windows 下请以脚本文件方式运行（勿用 heredoc）
