# 头条号主页数据采集指南

## 抓取方式（实测）

- **用 `web.fetch`**：头条 PC 主页是 JS 渲染的 SPA，`web.fetch` 的渲染管线能拿到完整内容（头像、简介、粉丝数、内容流）。
- **不要用 `curl`**：直接 curl 主页只返回约 5KB 的 JS 空壳；未登录 API（如 `/api/pc/list/user/feed`、`/api/pc/user/detail`）返回空、404 或 `login_required`。移动端 `m.toutiao.com` 也 404。
- 页面渲染成功的标志：返回里出现账号名、"XX获赞 XX粉丝 XX关注"、简介和内容流。

## Tab URL 模式

主页 URL 形如 `https://www.toutiao.com/c/user/token/{TOKEN}/`。在后面加 query 参数切换栏目（实测有效）：

| 栏目 | URL 后缀 |
|---|---|
| 微头条（默认主页即此流） | 无参数 / `/?enter_from=mp_profile` |
| 文章 | `/?tab=article` |
| 视频 | `/?tab=video` |
| 合集 | `/?tab=collection` |

`?tab=weitoutiao` 返回与默认主页相同，无需单独抓。

## 分页读取

每个 tab 的 `web.fetch` 返回 `total_length`，用 pagination 的 `offset` 续读直到 `end_offset >= total_length`。单次建议 limit 6000-9000 token，减少图片观察次数。

## 每个 tab 要提取的字段

**主页头**：账号名、获赞数、粉丝数、关注数、简介全文、头像描述、可见内容时间窗。

**文章 tab**：逐条记录 标题、阅读数、发布日期、评论数、配图内容描述（重点判断配图是否与主题相关）。

**视频 tab**：逐条记录 标题（系列名）、时长、播放数、发布日期、封面风格、话题标签。

**微头条流**：逐条记录 全文要点、人设自称（如"周哥"）、赞数、评论数、日期、话题标签列表（数标签数量、记录是否有与正文无关的蹭热点标签）。

**合集 tab**：合集名、播放量、创建日期、条数。

## 采集后统计

把文章阅读数、视频播放数分别列成数组，交给 `scripts/tally.py` 计算均值、中位数和区间分布，避免口算出错。
