# 部署说明 · 交给 Claude Code 执行

这个文件夹是一个完整的网站项目。你不需要懂代码——把下面这段话**原样复制给 Claude Code**，它会一步步帮你部署。部署完成后，你会得到一个网址，发给朋友点开即用。

---

## 你需要先准备的

1. 一个 **GitHub 账号**（github.com 免费注册）。
2. 在电脑上装好 **Claude Code**。
3. 把这整个 `gold-sense-web` 文件夹放在你电脑上能找到的位置。

---

## 复制给 Claude Code 的指令

> 我有一个静态网站项目，在文件夹 `gold-sense-web` 里。请帮我把它部署到 GitHub Pages，并配置好每日自动更新数据。具体步骤：
>
> 1. 在这个文件夹里初始化 git 仓库，并在我的 GitHub 账号下创建一个新的公开仓库（名字用 `gold-sense`），把所有文件推上去。注意 `.github/workflows/update-data.yml` 这个文件要原样保留。
> 2. 帮我开启这个仓库的 GitHub Pages，部署来源选 `main` 分支的根目录（`/root`）。
> 3. 确认 Actions 已启用，并且仓库设置里 Workflow 的权限是「Read and write permissions」（这样定时任务才能把更新后的数据提交回仓库）。
> 4. 帮我手动触发一次 `Update gold data` 这个 workflow（在 Actions 标签页点 Run workflow），让它立刻抓一次真实数据，这样网站第一次打开就有数据，而不是显示「暂无数据」。
> 5. 等 workflow 跑完后，告诉我最终的网站访问网址（形如 `https://<我的用户名>.github.io/gold-sense/`）。
> 6. 打开那个网址确认能看到真实的金价和实际利率数据，而不是「Data unavailable」。如果显示无数据，帮我看 Actions 的日志排查 `scripts/fetch_data.py` 为什么没抓到。

---

## 部署后会发生什么（你不用管，自动的）

- 网站每天美东收盘后（UTC 22:30）自动抓一次 FRED 的最新数据，更新 `data/data.json`，网页随之刷新。
- 数据全部来自 FRED（圣路易斯联储），真实、免费、无需 API key。
- 抓不到的数据会显示「暂无数据 / Data unavailable」，**绝不编造数字**。

---

## 如果数据抓不到（备用方案）

FRED 的公开端点一般够用。万一 Actions 日志显示抓取失败，可以加一个免费的 FRED key 增强稳定性：

1. 去 https://fredaccount.stlouisfed.org/apikeys 免费申请一个 API key。
2. 在 GitHub 仓库的 Settings → Secrets and variables → Actions → New repository secret，名字填 `FRED_API_KEY`，值填你申请到的 key。
3. 重新运行一次 workflow。脚本会自动用这个 key 作为备用通道。

（这一步通常不需要，只在公开端点被限流时才用得上。）

---

## 项目文件说明（给好奇的你）

```
gold-sense-web/
├── index.html              ← 网站本体（读数据 + 你的框架规则引擎 + 中英双语）
├── FRAMEWORK.md            ← 你的完整分析框架（网站底部「阅读完整框架」链接到它）
├── data/
│   └── data.json           ← 真实数据，由每日任务自动更新（初始是空的占位）
├── scripts/
│   └── fetch_data.py       ← 抓 FRED 数据的脚本（GitHub 自动运行，不用你管）
└── .github/workflows/
    └── update-data.yml     ← 每日定时任务的配置
```

---

## 给朋友用

部署完成后，你只需要把那个网址（`https://<你的用户名>.github.io/gold-sense/`）发给朋友。他们点开就能用，不需要注册、不需要配任何东西、手机微信里也能打开。
