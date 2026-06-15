#!/usr/bin/env python3
"""
PDF论文全文 + 图片提取工具
用法：python extract_figures.py --pdf "论文路径.pdf" --output-dir "输出目录"
输出：JSON（full_text, figures列表, page_count）
"""

import os
import re
import json
import argparse
from pathlib import Path
import fitz  # PyMuPDF


def extract_full_text(doc):
    """提取PDF全文（所有页面文本拼接）"""
    pages_text = []
    for i, page in enumerate(doc):
        text = page.get_text()
        pages_text.append(f"--- 第 {i+1} 页 ---\n{text}")
    return "\n\n".join(pages_text)


def detect_all_figures(doc):
    """
    扫描所有页面，找出所有 Fig. X / Figure X 图注位置。
    返回列表：[{"num": 1, "page": 2, "caption_y0": 300.5, "caption_text": "...", "bbox": [...]}, ...]
    """
    pattern = re.compile(r'(?i)^(?:fig\.?|figure)\s*(\d+)\b')
    figures = []

    for page_idx, page in enumerate(doc):
        blocks = page.get_text("blocks")
        for b in blocks:
            if b[6] != 0:  # 非文本块跳过
                continue
            text = b[4].strip()
            m = pattern.search(text)
            if m:
                fig_num = int(m.group(1))
                figures.append({
                    "num": fig_num,
                    "page": page_idx + 1,
                    "caption_y0": b[1],
                    "caption_text": text[:200],  # 截取前200字防止过长
                    "bbox": [b[0], b[1], b[2], b[3]]
                })
    return figures


def extract_raster_image(page, caption_y0, min_width=150, min_height=150, max_dist=350):
    """方案A：在图注上方找内嵌栅格图片"""
    images = page.get_image_info(xrefs=True)
    valid_images = [img for img in images
                    if img['width'] > min_width and img['height'] > min_height]

    best_xref = None
    min_dist = float('inf')

    for img in valid_images:
        img_y1 = img['bbox'][3]
        dist = abs(caption_y0 - img_y1)
        if dist < min_dist and dist < max_dist:
            min_dist = dist
            best_xref = img['xref']

    return best_xref


def render_vector_screenshot(page, bbox, caption_y0, page_rect_width, zoom=2, look_up=450):
    """方案B：矢量图高清截屏"""
    crop_rect = fitz.Rect(
        max(0, bbox[0] - 50),
        max(0, caption_y0 - look_up),
        page_rect_width - 20,
        caption_y0
    )
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=crop_rect)
    return pix


def extract_figure(doc, fig_info, output_dir, verbose=True):
    """
    对单个fig_info尝试提取图片。先方案A（内嵌图片），失败则方案B（矢量截屏）。
    返回文件名或None。
    """
    fig_num = fig_info["num"]
    page_idx = fig_info["page"] - 1
    caption_y0 = fig_info["caption_y0"]
    page = doc[page_idx]

    # 方案A
    xref = extract_raster_image(page, caption_y0)
    if xref:
        try:
            base_image = doc.extract_image(xref)
            img_ext = base_image['ext']
            filename = f"fig_{fig_num}.{img_ext}"
            filepath = output_dir / filename
            with open(filepath, "wb") as f:
                f.write(base_image['image'])
            if verbose:
                print(f"  [OK] 图{fig_num} → 内嵌{img_ext.upper()} (第{page_idx+1}页)")
            return filename
        except Exception as e:
            if verbose:
                print(f"  [WARN] 图{fig_num} 内嵌图片提取失败: {e}")

    # 方案B
    try:
        bbox = fig_info["bbox"]
        pix = render_vector_screenshot(page, bbox, caption_y0, page.rect.width)
        filename = f"fig_{fig_num}_rendered.png"
        filepath = output_dir / filename
        pix.save(str(filepath))
        if verbose:
            print(f"  [OK] 图{fig_num} → 矢量截屏PNG (第{page_idx+1}页)")
        return filename
    except Exception as e:
        if verbose:
            print(f"  [FAIL] 图{fig_num} 矢量截屏失败: {e}")

    return None


def process_pdf(pdf_path, output_dir, verbose=True):
    """
    主处理函数：提取全文 + 检测并提取所有图片。
    返回结果字典。
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"📄 打开: {pdf_path.name}")

    doc = fitz.open(pdf_path)

    # 1. 提取全文
    if verbose:
        print("  → 提取全文...")
    full_text = extract_full_text(doc)

    # 2. 检测所有图片位置
    if verbose:
        print("  → 检测图片位置...")
    figures_raw = detect_all_figures(doc)

    # 3. 逐图提取
    figures_result = []
    for fig in figures_raw:
        filename = extract_figure(doc, fig, output_dir, verbose=verbose)
        figures_result.append({
            "num": fig["num"],
            "page": fig["page"],
            "caption_text": fig["caption_text"],
            "filename": filename,
            "extracted": filename is not None
        })

    page_count = doc.page_count
    doc.close()

    # 构建输出
    result = {
        "pdf_name": pdf_path.name,
        "pdf_stem": pdf_path.stem,
        "page_count": page_count,
        "full_text": full_text,
        "figures": figures_result,
        "text_length": len(full_text),
        "figure_count": len(figures_result),
        "extracted_count": sum(1 for f in figures_result if f["extracted"])
    }

    if verbose:
        print(f"  ✅ 完成：{result['page_count']}页, {result['figure_count']}张图检测, "
              f"{result['extracted_count']}张成功提取")
        print(f"  文本长度: {result['text_length']} 字符")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="PDF论文全文 + 图片提取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python extract_figures.py --pdf "paper.pdf" --output-dir "./W24/paper_assets/"
  python extract_figures.py --pdf "paper.pdf" --output-dir "./out/" --json-only
  python extract_figures.py --pdf "paper.pdf" --output-dir "./out/" --save-text
        """
    )
    parser.add_argument("--pdf", required=True, help="PDF文件路径")
    parser.add_argument("--output-dir", required=True, help="图片输出目录")
    parser.add_argument("--json-only", action="store_true",
                        help="只输出JSON到stdout，不保存文件")
    parser.add_argument("--save-text", action="store_true",
                        help="额外保存full_text为txt文件")
    parser.add_argument("--quiet", action="store_true",
                        help="静默模式，减少日志输出")

    args = parser.parse_args()

    verbose = not args.quiet

    result = process_pdf(args.pdf, args.output_dir, verbose=verbose)

    if args.json_only:
        print(json.dumps(result, ensure_ascii=False))
    else:
        # 保存JSON元数据
        json_path = Path(args.output_dir) / f"{result['pdf_stem']}_meta.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        if verbose:
            print(f"📋 元数据已保存: {json_path}")

        # 可选保存纯文本
        if args.save_text:
            txt_path = Path(args.output_dir) / f"{result['pdf_stem']}_full.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(result["full_text"])
            if verbose:
                print(f"📝 全文已保存: {txt_path}")

    # 退出码：完全不成功才非0
    if result["figure_count"] > 0 and result["extracted_count"] == 0:
        if verbose:
            print("⚠️  检测到图片但全部提取失败，请检查PDF格式")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
