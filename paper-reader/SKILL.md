---
name: paper-reader
description: "学术文献精读与深度拆解，从PDF论文提取文字和图片，按九大模块生成结构化HTML精读笔记。触发词：'精读论文', '文献精读', 'paper reader', '读这篇论文', '处理本周文献'。"
user_invocable: true
version: "1.0.2"
agent_created: true
---

# Paper Reader: 文献精读与认知重构

读论文不是做摘要，是猎取思想。本Skill把PDF论文拆解成「不懂这个领域的聪明人也能看懂并复述」的认知框架，最终输出带图片的结构化HTML精读笔记。

---

## 前置步骤：读取配置

开始前先读取项目根目录下的 `config.yaml`（如不存在则读取 `config.example.yaml` 并提示用户复制修改）。从配置中获取：

- `paths.python_exe` — Python 解释器路径
- `literature.pdf_dir` — PDF 论文存放目录（按 W{周号}/ 子目录组织）
- `literature.html_output_dir` — 精读 HTML 输出目录（按 W{周号}/ 子目录组织）

---

## 路径约定

| 用途 | 路径 | 说明 |
|------|------|------|
| PDF输入 | `{literature.pdf_dir}/W{周号}/` | 按ISO周号组织，如 W24。从 config.yaml 读取 pdf_dir |
| HTML输出 | `{literature.html_output_dir}/W{周号}/` | 自动创建对应周目录。从 config.yaml 读取 |
| 图片资源 | `{输出目录}/{论文名}_assets/` | 与HTML同目录下的assets子目录 |
| 提取工具 | `<SKILL_DIR>/assets/extract_figures.py` | PDF文字+图片提取脚本 |

**周号规则**：默认使用当前ISO周号（`python -c "import datetime; print(datetime.date.today().isocalendar()[1])"`）。用户可指定周号，如"处理W19的所有论文"。

> **路径说明**：所有路径通过项目根目录的 `config.yaml` 集中配置。安装后请复制 `config.example.yaml` 为 `config.yaml` 并修改其中的路径为你本机的实际路径。详见项目 README.md 的"安装与配置"章节。

---

## 触发条件

用户消息包含以下任一关键词时触发：
- "精读论文" / "文献精读" / "paper reader" / "paper reading"
- "读这篇论文" / "解析文献" / "拆解这篇文献"
- "处理本周文献" / "处理W{数字}的论文"

---

## 工作流（严格按此顺序执行）

### Phase 1: 确定范围并扫描

1. **确定周号**：
   - 若用户未指定，用 `python -c "import datetime; print(datetime.date.today().isocalendar()[1])"` 获取当前周
   - 格式化为 `W{周号}`（如 `W24`）

2. **扫描PDF**：
   - 用 `ls` 或 `Get-ChildItem` 列出 `{literature.pdf_dir}/W{周号}/*.pdf`
   - 若无PDF文件，告知用户并结束
   - 向用户展示待处理清单，**请求确认后再继续**

3. **创建输出目录**：
   - `mkdir -p "{literature.html_output_dir}/W{周号}"`

### Phase 2: 逐篇处理循环

对每个PDF文件，按以下子步骤执行：

#### 2a. 提取文字 + 图片

运行提取脚本：

```bash
"{python_exe}" \
  "<SKILL_DIR>/assets/extract_figures.py" \
  --pdf "{literature.pdf_dir}/W{周号}/{论文文件名}.pdf" \
  --output-dir "{literature.html_output_dir}/W{周号}/{论文名}_assets"
```

脚本输出：
- `{论文名}_meta.json` — 元数据（full_text, figures列表）
- 提取的图片文件（`fig_1.png`, `fig_2_rendered.png` 等）

**读取 `_meta.json`** 获取 full_text 和 figures 信息。

**扫描版PDF检测**（必须执行）：读取 `_meta.json` 后，检查 `text_length`。如果 `text_length < 500`（意味着几乎所有页面都无文字层，是扫描图片版PDF），**立即停止处理该篇**，告知用户：
> "这篇「{论文名}」是扫描图片版PDF，fitz 无法提取文字（仅 {text_length} 字符）。请替换为文字版PDF后重试。"
- 跳过该篇，继续处理列表中下一篇
- **严禁**尝试OCR、渲染页面截图等任何降级方案——这些不可靠且浪费时间

#### 2b. LLM深度分析

基于提取的 full_text，按**九大模块框架**（见下方）生成HTML格式的深度分析。

在分析中需要引用图片时，使用以下HTML格式（直接嵌入，无需占位符）：

```html
<div class="figure-container">
    <img src="{论文名}_assets/fig_3.png" alt="图3">
    <div class="figure-caption">
        <strong>图3：</strong> 原文Figure Caption的中文精准翻译
    </div>
</div>
```

**图片引用规则**：
- **仅在解释重要数据时穿插引用图片**，不需要把所有提取的图都放进去——只放文中分析讨论到的关键图表
- 检查 `_meta.json` 中 `figures` 数组，确认 `extracted: true` 的图片才引用
- 引用路径使用相对路径：`{论文名}_assets/{filename}`
- 若某张重要图片 `extracted: false`，尝试用Read工具读取PDF中对应页面截图作为备选，否则生成警告占位

#### 2c. 生成最终HTML

使用下方HTML模板，将2b的分析内容嵌入 `<body>` 标签，保存为：

```
{literature.html_output_dir}/W{周号}/{论文名}_精读.html
```

#### 2d. 进度反馈

每完成一篇，告知用户进度（如"W24 进度: 2/3"）。

---

## 九大模块分析框架

分析输出必须严格按以下结构组织，使用HTML `<h2>` ~ `<h4>` 标题层级。

### 01 论文速览

```html
<h2>《[期刊缩写]》[原论文题目中文翻译]</h2>

<h2><span class="section-title"><span class="section-num">01</span> 论文速览</span></h2>
<ul>
  <li><strong>期刊</strong>：[期刊全称]</li>
  <li><strong>题目</strong>：[英文原题]</li>
  <li><strong>团队</strong>：[核心机构 / 通讯作者]</li>
  <li><strong>链接</strong>：[DOI 或原文URL]</li>
</ul>
```

### 02 核心摘要

用3-5句大白话概括：这篇工作瞄准了什么痛点？提出了什么新解法？核心结论是什么？

### 03 具象锚点与研究动机

- **现实痛点**：给出具象的现实场景，说明当前瓶颈/前人卡在哪里的本质
- **科学问题与作者入口**：明确论文要解决的科学问题，作者从哪个角度切入？为什么这个切入点有戏？**必须从原文提取作者视角的论述**

### 04 核心方法与设计哲学

按逻辑拆解研究方法：
1. **核心机制（做了什么）**：输入输出、核心架构或实验流程
2. **设计理由（为什么这么做）**：解释作者放弃传统方案而选择当前设计的底层原因。**必须提取自原文，严禁AI先验知识臆断**。若原文未说明，明确标注"作者在文中未明确说明采用该设计的具体原因"
3. **公式/理论翻译**：若有核心公式，列出后用中文说明它在现实中代表什么意思。使用 `$$...$$` 和 `$...$` (KaTeX格式)

### 05 关键数据与实验结果

- **主干发现**：剔除凑数表格，只提炼让人"哇"的对比数据和消融实验
- **关键图表解析**：解释重要数据时穿插图片引用（只放文中讨论到的关键图，不需要每张都放）
- **反直觉现象（如有）**：原文中提到的意外发现或次要但有趣的结论

### 06 局限性与薄弱点批判

客观指出方法论约束、数据样本局限、偏见及研究空白。转述作者Limitation声明；若作者未提但存在明显推导不严密处，客观指出。

### 07 思想结晶与可迁移启发

- **底层洞见**：提炼全篇最值钱的认知结晶，脱离这篇论文依然成立的底层逻辑
- **实践启发**：落点在"能用"，探讨发现对实际应用、学术界的潜在贡献

### 08 关键引用

挑选原文中2-3处真正定义了思想形状的句子：
- **原文**：`"Original verbatim quote here..."`
- **精译**：用大白话精准翻译，不要生硬直译

### 09 面试官灵魂 Q&A

模拟对该领域有深度的专家/审稿人，针对核心机制、潜在漏洞、假设前提提出3-5个尖锐问题，并给出基于论文推演的参考答案。

---

## 核心红线（严禁违反）

1. **绝对原文溯源**：一切"为什么这么做"必须基于PDF原文提取。严禁脱离文档用AI先验知识主观臆断。原文没解释就标注"作者未明确说明"。
2. **零术语裸奔**：专业术语首次出现必须用大白话落地解释。
3. **拒绝学术八股**：严禁"近年来随着...的发展""值得注意的是"等无信息量套话。
4. **诚实与克制**：客观描述实验现象，严禁人为调和矛盾点或掩盖局限性。

---

## HTML模板

最终HTML必须使用以下模板结构，替换 `{title}` 和 `{body_content}`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 精读笔记</title>

    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"
        onload="renderMathInElement(document.body, {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '$', right: '$', display: false}
            ]
        });"></script>

    <style>
        :root { --primary: #2c3e50; --accent: #0070C0; --bg: #ffffff; }

        body {
            font-family: "Microsoft YaHei", "微软雅黑", sans-serif;
            line-height: 1.8; color: #333; max-width: 850px;
            margin: 0 auto; padding: 40px 20px; background-color: var(--bg);
            font-size: 17px;
        }

        /* 主标题 */
        h1 {
            font-size: 1.5em; color: var(--primary);
            font-weight: 700;
            border-bottom: 2px solid var(--accent);
            padding-bottom: 12px; margin-bottom: 30px;
        }

        /* 01-09 大标题 */
        h2 {
            font-size: 1.3em;
            margin-top: 2.5em; margin-bottom: 0.8em;
            text-align: center;
        }
        h2 .section-num {
            font-size: 1.4em; font-style: italic; color: var(--accent);
            margin-right: 12px; font-weight: 700;
            vertical-align: baseline;
        }
        h2 .section-title {
            display: inline-block;
            border-bottom: 2px solid var(--accent);
            padding-bottom: 1px;
            color: var(--accent);
        }

        /* 子标题 */
        h3 {
            font-size: 1.1em; color: var(--primary);
            margin-top: 1.5em; margin-bottom: 0.5em;
            border-bottom: 1px solid #f0f0f0;
            padding-bottom: 4px;
        }

        blockquote {
            border-left: 3px solid var(--accent);
            margin: 1em 0; padding: 0.5em 1em;
            background: #f0f7ff; color: #2c3e50;
            font-size: 16px;
        }

        .figure-container {
            margin: 30px 0; padding: 20px;
            background: #fafbfc; border: 1px solid #e2e8f0;
            border-radius: 8px; text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }
        .figure-container img {
            max-width: 100%; height: auto;
            border-radius: 4px; margin-bottom: 15px;
        }
        .figure-caption {
            font-size: 15px; color: #475569;
            line-height: 1.6; text-align: left;
            border-top: 1px dashed #cbd5e1; padding-top: 15px;
        }
        .warn-placeholder {
            background: #fef2f2; border: 1px solid #fca5a5;
            border-radius: 8px; padding: 20px; text-align: center;
            margin: 30px 0;
        }
    </style>
</head>
<body>
{body_content}
</body>
</html>
```

---

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| 指定周无PDF | 告知用户并列出有内容的最近周目录 |
| 扫描版PDF（text_length < 500） | **立即停止该篇**，告知用户替换为文字版PDF。严禁尝试OCR |
| 图片全部提取失败 | 标注警告但不阻断流程，继续生成纯文字HTML |
| 单篇PDF读取出错 | 跳过该篇，记录到终报告，继续处理剩余PDF |
| PyMuPDF未安装 | 指导用户安装：`pip install PyMuPDF` |
| 输出目录创建失败 | 检查磁盘空间和权限，报告具体错误 |

---

## 示例用法

```
用户: 处理本周文献
→ 自动检测当前周(如W24)，扫描{pdf_dir}/W24/*.pdf
→ 逐个提取→分析→生成HTML

用户: 处理W19的所有论文
→ 扫描{pdf_dir}/W19/*.pdf
→ 同上流程

用户: 精读这篇论文 {pdf_dir}/W24/corrosion_modeling.pdf
→ 单篇处理模式，直接对该文件执行2a-2c步骤
```
