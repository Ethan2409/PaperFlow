import pandas as pd
import re
import os
import sys
import json
import argparse
import yaml


def load_config(config_path=None):
    """加载 config.yaml。如果找不到，使用内置默认值。"""
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return None


def build_topic_configs_from_yaml(config):
    """从 config.yaml 构建评分词库。无配置文件时返回默认硬编码值。"""
    if not config or "scopus_topics" not in config:
        return _default_configs()

    result = {}
    for topic in config["scopus_topics"]:
        name = topic["name"]
        top_journals = topic.get("top_journals", [])
        high_journals = topic.get("high_journals", [])
        extra_journals = [j for j in top_journals if j not in _default_top_journals()]

        result[name] = {
            "rel_plus": [rf"\b{kw.replace('?', r'?')}\b" if "?" not in kw else kw for kw in topic.get("relevance_keywords", [])],
            "qual_plus": [rf"\b{kw}\b" for kw in topic.get("quality_keywords", [])],
            "extra_journals": extra_journals,
        }
    return result if result else _default_configs()


def _default_top_journals():
    return [
        "corrosion science", "acta materialia", "electrochimica acta",
        "npj materials degradation", "journal of materials science & technology",
        "journal of the electrochemical society"
    ]


def _default_configs():
    """默认评分词库（材料腐蚀领域），作为 config.yaml 缺失时的后备。"""
    return {
        "纯点蚀研究": {
            "rel_plus": [r'\bpitting\b', r'\blocalized corrosion\b', r'\bpassivity\b', r'\bmicro-galvanic\b', r'\binclusions?\b', r'\bpit\b'],
            "qual_plus": [r'\bin[- ]situ\b', r'\bxps\b', r'\bapt\b', r'\bhrtem\b', r'\beis\b'],
            "extra_journals": []
        },
        "点蚀预测": {
            "rel_plus": [r'\bphase[- ]field\b', r'\bcellular automata\b', r'\bnernst-planck\b', r'\bfem\b', r'\bpinn\b', r'\bneural networks?\b', r'\bu-net\b', r'\bdeep learning\b'],
            "qual_plus": [r'\bexperimental validation\b', r'\bmechanism-driven\b', r'\bphysics-informed\b', r'\bsegmentation\b', r'\bimage processing\b'],
            "extra_journals": ["computational materials science"]
        },
        "通用数字孪生": {
            "rel_plus": [r'\bdigital twin\b', r'\bsurrogate models?\b', r'\breal-time\b', r'\biot\b', r'\bfno\b', r'\bu-net\b'],
            "qual_plus": [r'\bsystem architecture\b', r'\bmulti-physics\b', r'\blatency\b'],
            "extra_journals": ["ieee internet of things", "computer-aided design"]
        },
        "默认": {
            "rel_plus": [r'\bcorrosion\b', r'\bpitting\b', r'\bdigital twin\b', r'\bpredict\b', r'\bneural networks?\b'],
            "qual_plus": [r'\bin[- ]situ\b', r'\bsimulation\b', r'\bdeep learning\b'],
            "extra_journals": []
        }
    }


def evaluate_papers(file_path, cfg, topic_name):
    """对单篇 CSV 文件打分。"""
    # 1. 强鲁棒性数据读取
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
    except:
        df = pd.read_csv(file_path, encoding='latin1')

    def get_col(possible_names):
        for name in possible_names:
            if name in df.columns:
                return name
        return None

    col_title, col_abs = get_col(['Title', '文献标题']), get_col(['Abstract', '摘要'])
    col_journal = get_col(['Source title', '来源出版物名称'])
    col_year = get_col(['Year', '年份'])
    col_authors, col_doi = get_col(['Authors', '作者']), get_col(['DOI'])

    for col in [col_title, col_abs, col_journal, col_year, col_authors, col_doi]:
        if col is not None:
            df[col] = df[col].fillna('').astype(str)

    results = []

    def count_matches(text, patterns):
        score = 0
        for p in patterns:
            if re.search(p, text):
                score += 1.5
        return score

    # 2. 遍历打分
    for _idx, row in df.iterrows():
        title = row[col_title] if col_title else ""
        abstract = row[col_abs] if col_abs else ""
        text = (title + " " + abstract).lower()
        journal = (row[col_journal] if col_journal else "").lower()

        if not title:
            continue

        # --- 维度 1: 相关性 ---
        rel_score = min(5.0, count_matches(text, cfg['rel_plus']))

        # --- 维度 2: 影响力 ---
        imp_score = 1.0
        top_j = _default_top_journals() + cfg.get('extra_journals', [])
        high_j = ['corrosion', 'materials & design']

        if any(tj in journal for tj in top_j):
            imp_score = 3.0
        elif any(hj in journal for hj in high_j):
            imp_score = 2.0

        # --- 维度 3: 研究质量 ---
        qual_score = 1.0

        if count_matches(text, cfg['qual_plus']) > 0:
            qual_score += 1.0

        if re.search(r'\breview\b', title.lower()) and count_matches(text, cfg['qual_plus']) == 0:
            qual_score -= 0.5

        qual_score = min(2.0, max(0.0, qual_score))

        # --- 总分 ---
        results.append({
            'title': title,
            'authors': row.get(col_authors, ''),
            'journal': journal.title(),
            'year': row.get(col_year, "N/A"),
            'doi': row.get(col_doi, ''),
            'abstract': abstract,
            'score': round(rel_score + imp_score + qual_score, 1)
        })

    top_papers = sorted(results, key=lambda x: x['score'], reverse=True)[:10]
    return topic_name, len(results), top_papers


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(description="Scopus 文献评分引擎")
    parser.add_argument("--config", help="config.yaml 路径（可选，缺省使用内置默认值）")
    parser.add_argument("csv_files", nargs="+", help="CSV 文件路径列表")
    args = parser.parse_args()

    # 加载配置
    conf = load_config(args.config)
    all_configs = build_topic_configs_from_yaml(conf)

    results = []
    for csv_path in args.csv_files:
        if not os.path.exists(csv_path):
            print(json.dumps({"error": f"File not found: {csv_path}"}, ensure_ascii=False), file=sys.stderr)
            continue

        # 从文件名识别主题
        filename = os.path.basename(csv_path)
        topic = "默认"
        for topic_name in all_configs:
            if topic_name in filename:
                topic = topic_name
                break

        cfg = all_configs.get(topic, all_configs["默认"])
        topic_name, total, top10 = evaluate_papers(csv_path, cfg, topic)
        results.append({"topic": topic_name, "total": total, "top10": top10})

    print(json.dumps(results, ensure_ascii=False, indent=2))
