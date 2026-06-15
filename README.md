# PaperFlow

> 半自动化文献筛选与精读工作流 —— 从 Scopus 周更 CSV 到结构化精读笔记。

## 这是什么？

PaperFlow 是一套 [WorkBuddy](https://workbuddy.ai) / [Claude Code](https://claude.ai/claude-code) 的 Skill 集合，把"读文献"拆成两步流水线：

1. **scopus-subscription**：喂给它 Scopus 周更推送的 CSV 文献列表，自动评分（0-10 分）、排序，生成 Obsidian Markdown 推荐笔记
2. **paper-reader**：喂给它下载好的 PDF 论文，按九大模块深度拆解，输出带图片、公式、SVG 可视化、Q&A 的自包含 HTML 精读笔记

读论文不是做摘要，是猎取思想。这两个 Skill 把别人的发现拆解成你能用的认知。

## 为什么是"半自动"？

不是技术做不到全自动。是**故意的**。

| 半自动策略 | 全自动搜索+下载 | 结论 |
|-----------|---------------|------|
| 人工下载 PDF（5 秒/篇） | AI 代理模拟浏览器下载（易失败、慢） | 人工快得多 |
| 一次性 token 消耗 ~30K/周 | 含搜索+下载 ~200K/周 | 省 85% token |
| PDF 下载走校园网/VPN，零权限问题 | 国外 API 无校园网权限，认证失败率高 | 无痛 |
| 你对哪些论文进入精读有完全控制权 | AI 自动筛选可能漏掉重要文献 | 可控 |

人工下载 PDF 这一步，恰好是性价比最高的"人机分工边界"。

## 项目亮点

- **智能评分引擎**：3 维度评分（相关性 50% + 影响力 30% + 研究质量 20%），关键词匹配 + 期刊分级，纯 Python 本地运行，不需要任何 API
- **九大模块精读框架**：从"论文速览"到"面试官灵魂 Q&A"，让不懂这个领域的人也能看懂并复述
- **自包含 HTML 输出**：KaTeX 数学公式渲染 + 论文原图嵌入 + SVG 可视化，双击即看，不依赖任何服务端
- **Obsidian 原生集成**：ISO 周号目录组织，WikiLink 双向链接，与你的知识库无缝对接
- **领域无关的核心框架**：预配置材料腐蚀领域关键词，更换关键词列表 = 更换研究领域，不需要改代码

### 工作流示意

```
周一：Scopus 邮件 → CSV → "处理本周文献" → 评分推荐 (scopus-subscription)
周三：手动下载 3-5 篇 PDF → 放入 Papers/W24/
周五："处理本周文献" → 精读笔记 HTML (paper-reader)
```

## 安装

### 前置要求

- [WorkBuddy](https://workbuddy.ai) 或 [Claude Code](https://claude.ai/claude-code)（已安装并配置）
- Python 3.8+（推荐 Anaconda）
- 安装依赖包：
  ```bash
  pip install PyMuPDF pandas pyyaml
  ```
- Obsidian（可选，用于笔记管理；不用的话把输出目录改成任意文件夹即可）

### 安装步骤

**1. 复制 Skill 到 WorkBuddy skills 目录：**

```bash
# Windows（PowerShell）
cp -r scopus-subscription/ ~/.workbuddy/skills/scopus-subscription/
cp -r paper-reader/ ~/.workbuddy/skills/paper-reader/

# macOS / Linux
cp -r scopus-subscription/ ~/.workbuddy/skills/scopus-subscription/
cp -r paper-reader/ ~/.workbuddy/skills/paper-reader/
```

**2. 创建配置文件：**

```bash
cd PaperFlow
cp config.example.yaml config.yaml
```

**3. 编辑 `config.yaml`，把路径改成你本机的实际路径：**

```yaml
paths:
  python_exe: "D:/ProgramFiles/Anaconda3/python.exe"   # 你的 Python 路径
  scopus_csv_dir: "C:/Users/你的用户名/Downloads/"     # CSV 下载目录
  obsidian_vault: "E:/Obsidian/"                       # Obsidian Vault 目录

literature:
  pdf_dir: "{paths.obsidian_vault}/Literature/Papers/"
  summary_dir: "{paths.obsidian_vault}/Literature/Summary/"
  html_output_dir: "{paths.obsidian_vault}/Literature/Paper_reader/"
```

**4. 重启 WorkBuddy，Skill 自动生效。**

### 路径说明

所有路径集中在 `config.yaml` 里管理，不需要翻两个 `SKILL.md` 一个个改：

| 变量 | 作用 | 说明 |
|------|------|------|
| `paths.python_exe` | Python 解释器 | 需要安装了 PyMuPDF 和 pandas 的 Python |
| `paths.scopus_csv_dir` | CSV 下载目录 | Scopus 邮件推送 CSV 保存的位置 |
| `paths.obsidian_vault` | Obsidian Vault | 不用 Obsidian 改成任意文件夹 |
| `literature.pdf_dir` | PDF 存放目录 | 按 W{周号}/ 组织，如 `W24/` |
| `literature.summary_dir` | 评分推荐输出 | Markdown 笔记输出位置 |
| `literature.html_output_dir` | 精读 HTML 输出 | 按 W{周号}/ 组织 |

## 使用

### scopus-subscription：文献筛选

在 WorkBuddy / Claude Code 中输入：

```
处理本周文献
```

Skill 会自动：
1. 扫描 `scopus_csv_dir` 中的 Scopus CSV 文件
2. 运行评分引擎，按 3 维度打分排序
3. 生成 Top 10 推荐笔记（Top 3 附带详细分析）
4. 保存到 Obsidian

### paper-reader：深度精读

**批量处理本周所有 PDF：**

```
处理本周文献
```

（当 PDF 目录中有待处理的论文时触发）

**单篇精读：**

```
精读这篇论文 E:/Obsidian/Literature/Papers/W24/my_paper.pdf
```

Skill 会自动：
1. 用 PyMuPDF 提取 PDF 全文 + 所有图片
2. 按九大模块生成深度分析
3. 输出自包含 HTML（KaTeX 公式 + 论文原图 + SVG 可视化）
4. 保存到 Paper_reader 目录，ISO 周号组织

### 典型周工作流

```
周一：收到 Scopus 邮件 → 下载 CSV → 说"处理本周文献" → 获取 Top 10 推荐
周二-周四：根据推荐手动下载 3-5 篇 PDF → 放入 Papers/W{周号}/
周五：说"处理本周文献" → 阅读生成的 HTML 精读笔记
```

## 隐私与安全检查

本项目**不包含**任何敏感信息：

- [x] 无 API 密钥（评分全程本地 Python 运行，不调用任何外部 API）
- [x] 无硬编码用户路径（全部通过 `config.yaml` 集中配置）
- [x] 无个人身份信息（无邮箱、无账号、无手机号）
- [x] 无第三方服务凭据（无微信 AppID、无 GitHub Token 等）
- [x] `config.yaml`（你的私人配置文件）已被 `.gitignore` 排除，不会被提交到 Git
- [x] 所有路径引用均为变量（`{paths.xxx}`），实际值由用户自行填写

**安全措施**：
- `.gitignore` 排除了 `config.yaml`、`.env`、`__pycache__/`、`*.pyc` 等文件
- 项目根目录仅保留 `config.example.yaml` 作为填写模板

## 适配到你的研究领域

PaperFlow 的核心评分框架和精读框架是**领域无关**的。只要你有一个文献来源（CSV 格式或直接放 PDF），三步就能适配：

### 第一步：准备你的文献来源

- **CSV 方式**（用 scopus-subscription）：Scopus、Web of Science、PubMed、CNKI 等任何能导出 CSV 的文献数据库都可以，只需包含"标题"和"摘要"两列
- **PDF 方式**（仅 paper-reader）：直接在 PDF 目录中放论文，跳过评分

### 第二步：修改关键词配置

编辑 `config.yaml` 中的 `scopus_topics` 部分：

```yaml
scopus_topics:
  - name: "你的研究领域"
    csv_filename: "your_field.csv"
    relevance_keywords:
      - "your_keyword_1"
      - "your_keyword_2"
    quality_keywords:
      - "in-situ"
      - "experimental validation"
    top_journals:
      - "Nature"
      - "Science"
      - "Your Field Top Journal"
    high_journals:
      - "Your Field Good Journal"
```

### 第三步：让 AI 帮你自动适配

把 `SKILL.md` 和 `prompt.md` 喂给 WorkBuddy / Claude Code，告诉它：

> "我研究的是 [你的领域]，请根据这两个 Skill 内容，帮我调整评分关键词和推荐模板。"

Agent 会自动分析框架，生成适配你领域的版本。

### 核心原理

评分引擎（`score.py`）本质是：
- 正则表达式关键词匹配 → 相关性分数
- 期刊名称分级匹配 → 影响力分数
- 方法学关键词检测 → 质量分数

更换关键词列表 = 更换研究领域，不用改代码。

## 致谢

本项目的设计深受以下两个优秀项目的启发，特此致谢。

### 来自 [PaperReading-skills](https://github.com/Linchunhui/PaperReading-skills) (by Linchunhui)

PaperReading-skills 是论文精读 Skill 的标杆之作，paper-reader 从中借用了以下核心思想：

| 借用的元素 | 在 PaperFlow 中的体现 |
|-----------|---------------------|
| "读论文不是做学术，是猎取思想"的核心理念 | paper-reader SKILL.md 开篇即引用 |
| 10 章结构化分析框架 | paper-reader 的九大模块是对 10 章的工程化精简：合并 Motivation+现存问题为 03 具象锚点，保留其余核心结构 |
| 12 条质量检查红线（口语检验、零术语裸奔、短词优先、一句一事等） | paper-reader 的 4 条核心红线是对 12 条的领域化精炼 |
| "Motivation as anchor" 叙事技术 | paper-reader 专设 03 模块"具象锚点与研究动机"，贯穿全文 |
| 公式双规则：LaTeX + 中文白话翻译 | paper-reader HTML 模板要求每条公式后跟中文翻译，KaTeX 渲染 |
| 自包含 HTML 输出方案（CDN KaTeX + 内联 CSS） | paper-reader 完全继承此技术方案 |
| SVG 可视化替代表格复制 | paper-reader 在实验分析中使用内嵌 SVG |
| PDF 图片提取思路 | paper-reader 的 `extract_figures.py` 借鉴了其图片处理方案 |
| "面试官灵魂 Q&A" 章节设计 | paper-reader 的 09 模块直接继承 |

### 来自 [evil-read-arxiv](https://github.com/juliye2025/evil-read-arxiv) (by juliye2025)

evil-read-arxiv 是论文自动化工作流先驱，scopus-subscription 从中借用了以下核心思想：

| 借用的元素 | 在 PaperFlow 中的体现 |
|-----------|---------------------|
| 多维度论文评分机制（相关性+影响力+质量+新近性） | scopus-subscription 的三维评分是对四维的裁剪（去掉新近性——周更推送本身即是最新） |
| Obsidian 集成与 WikiLink 组织 | scopus-subscription 生成的推荐笔记采用 Obsidian WikiLink 格式 |
| Python 脚本评分架构 | `score.py` 借鉴了 `search_arxiv.py` 的模块化评分设计 |
| ISO 周号文件组织 | paper-reader 的 PDF 输入和 HTML 输出均按 ISO 周号组织目录 |
| 配置文件驱动设计 | `config.example.yaml` 架构借鉴了 evil-read-arxiv 的配置化理念 |
| 批量处理多篇论文 | 两个 Skill 均支持批量处理（一次处理一个 CSV / 一个周目录） |
| Top N 推荐输出格式 | scopus-subscription 的 Top 10 推荐借鉴了 start-my-day 的 Top N 设计 |

### PaperFlow 的独立创新

除上述借鉴外，以下为独立设计：

- **Scopus CSV 作为数据源**（非 arXiv API）：适配国内研究者通过邮件推送获取文献的实际场景
- **半自动策略**：人工下载 PDF + AI 精读分析，兼顾 token 效率和校园网权限
- **材料腐蚀领域专精**：预配置三套关键词集（纯点蚀研究 / 点蚀预测 / 通用数字孪生）
- **CSV 评分 + LLM 分析混合管道**：Python 量化评分 + 大模型语义总结

## License

MIT
