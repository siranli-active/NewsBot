# NewsBot（RSS → DeepSeek → Telegram 中文早报）

这是一个基于 Python 3.11 的早报项目：从 RSS 新闻源收集候选新闻，可选用 DeepSeek 根据本地 `profile.xml` 的最小化画像筛选、翻译和总结，再发送到 Telegram。

## 功能

- 从 `sources.yml` 读取 RSS 源
- 使用 `feedparser` 抓取新闻
- 按标题+链接去重
- 优先保留最近 24 小时新闻；无发布时间新闻保留但排后
- 默认收集 30 条普通新闻候选，再输出最多 16 条最终新闻
- 最终新闻尽量覆盖财经、时政、AI科技、医疗卫生、自然科学五类，其中财经、时政、AI科技在候选充足时各至少 4 条，医疗卫生和自然科学在候选充足时各 2 条
- 配置 DeepSeek 后，根据 `profile.xml` 的最小化画像筛选重要新闻、翻译英文新闻、生成按分类组织的重点方向
- 未配置 DeepSeek 时，自动使用本地规则 fallback 生成中文简报
- 发送到 Telegram Bot

## 环境要求

- Python 3.11

## 安装

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .[dev]
```

## 配置 RSS 源

编辑 `sources.yml`：

```yml
sources:
  - name: BBC World
    category: 时政
    url: https://feeds.bbci.co.uk/news/world/rss.xml
```

## 配置环境变量

Telegram 发送需要：

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

DeepSeek 个性化筛选可选：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_API_BASE`：可选，默认使用 DeepSeek OpenAI-compatible API base
- `DEEPSEEK_MODEL`：可选，默认 `deepseek-v4-flash`
- `PROFILE_XML_PATH`：可选，默认 `profile.xml`

本地可在 shell 中设置：

```bash
export TELEGRAM_BOT_TOKEN="你的token"
export TELEGRAM_CHAT_ID="你的chat_id"
export DEEPSEEK_API_KEY="你的DeepSeek API key"
```

GitHub Actions 里请在仓库 `Settings -> Secrets and variables -> Actions` 中添加同名 secrets。

`profile.xml` 会在本地先被最小化，不会把完整 XML 原文直接发送给 DeepSeek。最小化画像可以包含持仓和持仓比例，但不会包含收益率、设备细节或无关系统指令。

## 运行参数

```bash
python main.py --dry-run
python main.py --test
python main.py --max-items 16
python main.py --candidate-items 30
```

- `--test`：测试模式，只发送最多 3 条新闻，标题加【测试】，并跳过 DeepSeek 调用
- `--dry-run`：只在终端打印，不发送 Telegram
- `--max-items N`：指定最终最多发送多少条普通新闻
- `--candidate-items N`：指定 DeepSeek 筛选前最多收集多少条候选新闻

## 三种测试方法

1. 本地 dry-run 测试

```bash
python main.py --dry-run
```

2. 本地 Telegram 测试

```bash
python main.py --test
```

3. GitHub Actions 手动测试

- 打开 GitHub 仓库 `Actions`
- 选择 `Daily Morning Brief`
- 点击 `Run workflow`

## 自动部署（GitHub Actions）

工作流文件：`.github/workflows/daily_brief.yml`

- 包含 `workflow_dispatch`（手动触发）
- 包含定时触发
- 通过缓存 sent marker 限制同一伦敦日期只发送一次
