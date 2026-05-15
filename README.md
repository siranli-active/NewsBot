# NewsBot（RSS → Telegram 中文早报）

这是一个基于 Python 3.11 的免费早报项目，只使用 RSS 新闻源，不调用任何 AI API。

## 功能

- 从 `sources.yml` 读取 RSS 源
- 使用 `feedparser` 抓取新闻
- 按标题+链接去重
- 优先保留最近 24 小时新闻；无发布时间新闻保留但排后
- 默认最多发送 10 条（可通过参数覆盖）
- 规则生成“今日重点”（category 频次最高方向 + 前 3 条标题）
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
    url: https://feeds.bbci.co.uk/news/world/rss.xml
```

## 配置 Telegram Secrets

程序从环境变量读取：

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

本地可在 shell 中设置：

```bash
export TELEGRAM_BOT_TOKEN="你的token"
export TELEGRAM_CHAT_ID="你的chat_id"
```

GitHub Actions 里请在仓库 `Settings -> Secrets and variables -> Actions` 中添加同名 secrets。

## 运行参数

```bash
python main.py --dry-run
python main.py --test
python main.py --max-items 10
```

- `--test`：测试模式，只发送最多 3 条新闻，标题加【测试】
- `--dry-run`：只在终端打印，不发送 Telegram
- `--max-items N`：指定最多发送多少条

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
- 包含定时触发（通过 `0 7 * * *` 与 `0 8 * * *` 双触发 + Europe/London 时区判断，确保在伦敦时间早上 8 点执行）
