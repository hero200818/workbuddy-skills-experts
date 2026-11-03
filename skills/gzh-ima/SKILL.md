---
name: gzh-ima
display_name: ima 知识库入库
display_name_en: ima Knowledge Base Upload
description: "把本地文件入库到 ima 知识库（含腾讯云 COS 上传）。当用户要入 ima 库、上传知识库、把文章存进 ima、ima 入库、add_knowledge、COS 上传 403、SignatureDoesNotMatch 时使用。核心价值在 COS 临时密钥签名那段多套一层 StringToSign——少一层就 403，自己摸索极费时间；外加临时密钥上传完立刻删的防护规则。三步：create_media(MCP) → 本脚本上传 COS → add_knowledge(MCP)。纯标准库实现，零依赖，与具体账号无关（密钥从 MCP 每次临时下发）。触发词：ima、知识库、入库、add_knowledge、COS、SignatureDoesNotMatch、临时密钥、media_id。"
description_zh: ima 知识库入库三步（create_media→COS上传→add_knowledge），重点在 COS 签名多套一层的坑。
description_en: Upload documents into an ima knowledge base via COS, with the correct temp-key signing.
category: productivity
version: 1.0.0
author: 读读书悦悦己
agent_created: true
---

# ima 知识库入库

把本地文件（md / 图片 / pdf…）存进 ima 知识库。三步，中间那步的签名是唯一的坑。

## 什么时候用

- 要把写好的文章、文档、图片存进 ima 知识库做检索/引用
- COS 上传报 `403 SignatureDoesNotMatch`（几乎都是签名那一层少了一环）
- 想把入库流程自动化，但不知道临时密钥怎么用

## 三步流程

```
create_media(MCP) → 存 cred.json → python ima_put.py cred.json 文件 → add_knowledge(MCP)
```

| 步 | 工具 | 产出 |
|---|---|---|
| 1. create_media | MCP（`mcp__ima-mcp__create_media`） | 返回整段 JSON：含 `media_id` 与 `cos_credential` |
| 2. 上传 COS | 本脚本 `ima_put.py` | 把文件 PUT 到 COS 桶 |
| 3. add_knowledge | MCP（`mcp__ima-mcp__add_knowledge`） | 把 media_id 挂进指定知识库 |

## 用法

```bash
# 第 1 步之后：把 MCP 返回的 JSON 整段存成 cred.json
python ima_put.py cred.json 本地文件.md --ct text/markdown
# → 打印 media_id，拿它去调 add_knowledge
# → 入库完立刻删 cred.json
```

参数：

| 参数 | 说明 |
|---|---|
| `cred` | 第 1 步的 JSON（含 `media_id` + `cos_credential`；只给 `cos_credential` 对象也行） |
| `file` | 要上传的本地文件 |
| `--ct` | Content-Type，默认按扩展名推断（md→text/markdown、jpg→image/jpeg…） |

## 唯一的坑：COS 签名多套一层（不记住必 403）

临时密钥签名是**两层 HMAC**，少一层就 `SignatureDoesNotMatch`：

```
SignKey      = HMAC-SHA1(secret_key, key_time)          # 第一层
HttpString   = "put\n" + uri + "\n\n" + enc_headers + "\n"
StringToSign = "sha1\n" + key_time + "\n" + SHA1(HttpString) + "\n"   # ← 必须多这一层
Signature    = HMAC-SHA1(SignKey, StringToSign)          # 第二层
```

最容易漏的就是 `StringToSign` 外面那层 `sha1\n + key_time + \n + … + \n`——
直接拿 `SHA1(HttpString)` 当 `StringToSign` 去签，必 403。本脚本 `build_auth()` 已经是正确实现，
**改签名逻辑前先读这段，别"优化"掉那层。**

header 参与签名的只有两项：`host` 和 `x-cos-security-token`，`q-header-list=host;x-cos-security-token`。

## 防护规则

1. **临时密钥即用即删**：`cred.json` 含 secret_key / token，上传完立刻 `rm`，绝不准入库或提交
   （本项目的 `.gitignore` 已屏蔽 `cred*.json`）
2. **同名覆盖**：add_knowledge 用 `duplicate_name_strategy=DUPLICATE_NAME_STRATEGY_REPLACE`，
   同名文件原地覆盖，不会新增重复条目——适合"修订后重传"
3. **大文件超时**：urlopen 超时设 180s；几 MB 的 md 没问题，超大文件另想办法

## 验收

1. 第 2 步打印 `✓ 上传成功 200`
2. 第 3 步 add_knowledge 返回成功，去知识库网页能看到该条目
3. `cred.json` 已删除，仓库里搜不到密钥

## 环境

纯标准库（`urllib` / `hmac` / `hashlib` / `json`），Python 3 即可，零 pip 依赖。
不绑定任何账号——密钥每次 MCP 临时下发，换账号零改动。
