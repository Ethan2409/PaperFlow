---
name: scopus-subscription
description: >
  Scopus 周更文献自动评分与 Obsidian 推荐笔记生成。当用户说"处理本周文献"、
  "文献推送处理"、"生成文献推荐"、"更新 Scopus 推送"或类似表述时触发。
agent_created: true
---

# scopus-subscription

Scopus 周更文献自动评分与 Obsidian 推荐笔记生成。

## 前置步骤：读取配置

开始前先读取项目根目录下的 `config.yaml`（如不存在则读取 `config.example.yaml` 并提示用户复制修改）。从配置中获取：

- `paths.scopus_csv_dir` — Scopus CSV 下载目录
- `paths.python_exe` — Python 解释器路径
- `literature.summary_dir` — 推荐笔记输出目录（在 Obsidian Vault 内）

## 触发条件

当用户说"处理本周文献"、"文献推送处理"、"生成文献推荐"、"更新 Scopus 推送"或类似表述时触发。

## 核心流程

### 步骤 1：确认 CSV 文件

从 `config.yaml` 的 `scopus_topics` 列表中读取所有主题。对每个主题，拼接路径：

```
{scopus_csv_dir}/{csv_filename}
```

如果某个 CSV 不存在，跳过该主题并告知用户，继续处理其余文件。全部不存在则报错终止。

### 步骤 2：运行评分引擎

使用配置文件中的 Python 解释器执行 `scripts/score.py`：

```
{python_exe} <SKILL_DIR>/scripts/score.py --config <项目根目录>/config.yaml "csv1" "csv2" "csv3"
```

score.py 输出 JSON 数组，每个元素包含 `topic`、`total`（论文总数）、`top10`（评分最高的 10 篇论文，每篇含 title/authors/journal/year/doi/abstract/score）。

**静默执行：禁止向用户展示代码、运行日志或评分细节。**

### 步骤 3：读取输出格式规范

读取 `prompt.md`，严格按其定义的模板生成 Markdown。核心格式：

- **概览**：主题名、处理论文数、Top 10 最高分、新趋势总结（从 Top 10 摘要中提炼 2-3 句）
- **Top 3 论文**：一句话总结 + 核心贡献（具体数据/方法） + 详细分析（方法亮点、关联启发）
- **第 4-10 篇**：作者/期刊/年份/DOI/评分 + 一句话总结 + 核心贡献（不含详细分析）
- 评分维度：相关性 50%（5分）+ 影响力 30%（3分）+ 研究质量 20%（2分）

### 步骤 4：生成 Markdown 文件

对 score.py 返回的每个主题：

1. 计算当前 ISO 周数：`python -c "import datetime; print(datetime.date.today().isocalendar()[1])"`
2. 文件名格式：`W{周数}-{topic}.md`，如 `W24-点蚀预测.md`
3. 保存到 `{literature.summary_dir}`，目录不存在则自动创建
4. 同名文件直接覆盖

### 步骤 5：汇报结果

简洁告知处理结果：

```
处理完成，已生成 X 个文件：
  - {summary_dir}/W24-点蚀预测.md（共 Y 篇文献，Top 10 最高分 Z.Z）
  - ...
```

## 约束

1. 评分过程对用户完全透明无感 — 禁止暴露代码或运行日志
2. 每篇论文的一句话总结基于摘要内容，禁止凭空编造
3. 新趋势总结综合 Top 10 摘要提炼，不简单罗列
4. 自然语言内容使用简体中文
5. 论文标题和期刊名保留原文，不翻译
6. 评分保留一位小数，格式为 `X.X/10`
