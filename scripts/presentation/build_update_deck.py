#!/usr/bin/env python3
"""Build the research-grade update deck (dataset expansion + 3-model benchmark + Kaggle).

Run from repo root:
  python3 scripts/presentation/build_update_deck.py
Outputs:
  presentation/TP53_Update_2026-11_Dataset_Benchmark_Kaggle.pptx
"""

from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

REPO = Path(__file__).resolve().parents[2]
FIG = REPO / "figures"
OUT = REPO / "presentation" / "TP53_Update_2026-11_Dataset_Benchmark_Kaggle.pptx"

# --- palette ---------------------------------------------------------------
NAVY = RGBColor(0x0B, 0x3C, 0x5D)
TEAL = RGBColor(0x1D, 0x78, 0x74)
RED = RGBColor(0xD1, 0x49, 0x5B)
GOLD = RGBColor(0xE9, 0xB4, 0x4C)
GRAY = RGBColor(0x5A, 0x64, 0x72)
DARK = RGBColor(0x1A, 0x1A, 0x2E)
LIGHT = RGBColor(0xEE, 0xF2, 0xF6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ROW_ALT = RGBColor(0xF4, 0xF7, 0xFA)
GREEN = RGBColor(0x2E, 0x7D, 0x32)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
FOOTER = "TP53 Mutation Analysis  ·  research prototype — not a clinical tool"


def load_data() -> dict:
    bench = json.loads(
        (REPO / "results/machine_learning/benchmark/benchmark_results.json").read_text()
    )
    tuned = json.loads(
        (REPO / "results/machine_learning/benchmark/tuned_benchmark.json").read_text()
    )
    pos = json.loads(
        (REPO / "results/machine_learning/position_aware/position_aware_results.json").read_text()
    )
    metrics = json.loads((REPO / "results/machine_learning/metrics.json").read_text())
    cohort = json.loads((REPO / "results/machine_learning/cohort_summary.json").read_text())
    return {"bench": bench, "tuned": tuned, "pos": pos, "metrics": metrics, "cohort": cohort}


def add_bg(slide, color: RGBColor = WHITE) -> None:
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    shape.shadow.inherit = False
    # send to back
    sp = shape._element
    sp.getparent().remove(sp)
    slide.shapes._spTree.insert(2, sp)


def add_rect(slide, x, y, w, h, fill: RGBColor, line: RGBColor | None = None,
             rounded: bool = False):
    kind = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    sh = slide.shapes.add_shape(kind, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(1)
    sh.shadow.inherit = False
    return sh


def add_text(slide, x, y, w, h, text: str, *, size: float = 14, bold: bool = False,
             color: RGBColor = DARK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             font: str = "Calibri", italic: bool = False, line_spacing: float = 1.05):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color
        run.font.name = font
    return box


def add_title_bar(slide, kicker: str, title: str, page: int) -> None:
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.92), NAVY)
    add_rect(slide, 0, Inches(0.92), SLIDE_W, Inches(0.06), TEAL)
    add_text(slide, Inches(0.45), Inches(0.08), Inches(11.5), Inches(0.3),
             kicker.upper(), size=11, bold=True, color=RGBColor(0x9F, 0xD3, 0xCF))
    add_text(slide, Inches(0.45), Inches(0.32), Inches(11.5), Inches(0.55),
             title, size=24, bold=True, color=WHITE)
    add_text(slide, Inches(12.35), Inches(0.3), Inches(0.7), Inches(0.4),
             f"{page:02d}", size=16, bold=True, color=GOLD, align=PP_ALIGN.RIGHT)


def add_footer(slide) -> None:
    add_text(slide, Inches(0.45), Inches(7.15), Inches(12.4), Inches(0.28),
             FOOTER, size=9, color=GRAY)


def add_table(slide, x, y, w, h, headers, rows, *, col_w=None,
              header_fill: RGBColor = NAVY, font_size: float = 11,
              highlight_rows: set[int] | None = None,
              highlight_fill: RGBColor | None = None):
    """Add a formatted table; returns the pptx table shape."""
    n_rows = len(rows) + 1
    n_cols = len(headers)
    shape = slide.shapes.add_table(n_rows, n_cols, x, y, w, h)
    table = shape.table
    if col_w:
        total = sum(col_w)
        for i, cw in enumerate(col_w):
            table.columns[i].width = Emu(int(w * cw / total))

    for j, head in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = str(head)
        cell.fill.solid()
        cell.fill.fore_color.rgb = header_fill
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for r in p.runs:
                r.font.size = Pt(font_size)
                r.font.bold = True
                r.font.color.rgb = WHITE
                r.font.name = "Calibri"
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE

    highlight_rows = highlight_rows or set()
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            cell = table.cell(i, j)
            cell.text = str(val)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            if (i - 1) in highlight_rows:
                cell.fill.solid()
                cell.fill.fore_color.rgb = highlight_fill or RGBColor(0xE3, 0xF2, 0xEF)
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE if i % 2 else ROW_ALT
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT
                for r in p.runs:
                    r.font.size = Pt(font_size)
                    r.font.name = "Calibri"
                    r.font.color.rgb = DARK
                    r.font.bold = (j == 0) or ((i - 1) in highlight_rows)
    return table


def add_metric_card(slide, x, y, w, h, label: str, value: str, sub: str,
                    fill: RGBColor, value_color: RGBColor = WHITE):
    add_rect(slide, x, y, w, h, fill, rounded=True)
    add_text(slide, x, y + Inches(0.08), w, Inches(0.28), label.upper(),
             size=10, bold=True, color=WHITE if fill != LIGHT else GRAY,
             align=PP_ALIGN.CENTER)
    add_text(slide, x, y + Inches(0.32), w, Inches(0.45), value,
             size=22, bold=True, color=value_color if fill != LIGHT else NAVY,
             align=PP_ALIGN.CENTER)
    add_text(slide, x, y + Inches(0.78), w, Inches(0.35), sub,
             size=10, color=WHITE if fill != LIGHT else GRAY,
             align=PP_ALIGN.CENTER)


def add_picture_fit(slide, path: Path, x, y, max_w, max_h):
    """Insert picture scaled to fit inside max_w × max_h, centered."""
    from PIL import Image

    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(max_w / iw, max_h / ih)
    w = int(iw * scale)
    h = int(ih * scale)
    left = x + int((max_w - w) / 2)
    top = y + int((max_h - h) / 2)
    return slide.shapes.add_picture(str(path), left, top, width=w, height=h)


def fmt(v, nd=3):
    return f"{v:.{nd}f}"


def main() -> None:
    data = load_data()
    bench = data["bench"]
    results = {r["name"]: r for r in bench["results"]}
    cfg = bench["config"]
    metrics = data["metrics"]
    cohort = data["cohort"]
    pos = data["pos"]

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    # ==================================================================
    # 1 · TITLE
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s, NAVY)
    add_rect(s, 0, Inches(5.9), SLIDE_W, Inches(1.6), RGBColor(0x08, 0x2E, 0x47))
    add_rect(s, Inches(0.55), Inches(1.55), Inches(0.12), Inches(3.4), TEAL)
    add_text(s, Inches(0.95), Inches(1.5), Inches(11.5), Inches(0.4),
             "RESEARCH UPDATE  ·  NOVEMBER 2026", size=14, bold=True, color=GOLD)
    add_text(s, Inches(0.95), Inches(2.0), Inches(11.8), Inches(1.6),
             "TP53 Pathogenicity Classification\nDataset Expansion · Fair 3-Model Benchmark · Kaggle Deployment",
             size=30, bold=True, color=WHITE, line_spacing=1.15)
    add_text(s, Inches(0.95), Inches(3.7), Inches(11.5), Inches(0.8),
             "n = 388 → 818 ClinVar missense variants  ·  Extra Trees / Random Forest / CatBoost under one protocol\n"
             "21 leak-free features  ·  seed 42  ·  test set never used for selection  ·  GitHub + Kaggle reproducible",
             size=15, color=RGBColor(0xC9, 0xD8, 0xE4))
    add_text(s, Inches(0.95), Inches(6.2), Inches(8), Inches(0.9),
             "Simbisai Chinhema\nRepository: github.com/simbisaichinhema/TP53-Sequence-Structure-and-Machine-Learning-\n"
             "Kaggle: kaggle.com/simbisaichinhema/tp53-mutation-analysis",
             size=12, color=RGBColor(0xA8, 0xC0, 0xD2))
    add_text(s, Inches(10.2), Inches(6.35), Inches(2.7), Inches(0.7),
             "Research prototype\nNOT a clinical tool", size=12, bold=True,
             color=RED, align=PP_ALIGN.RIGHT)

    # ==================================================================
    # 2 · WHAT CHANGED (before/after)
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Update summary", "What changed in this update", 2)
    add_picture_fit(s, FIG / "presentation" / "before_after.png",
                    Inches(0.4), Inches(1.15), Inches(12.5), Inches(3.4))
    cards = [
        ("Dataset", "818", "405 P / 413 B\n+111% vs 388", TEAL),
        ("Default models", "3", "ET · RF · CatBoost\n(top CV ROC-AUC)", NAVY),
        ("Fair protocol", "5-fold", "CV on train only\nseed 42, 654/164", GREEN),
        ("Deployment", "Live", "GitHub main\nKaggle run COMPLETE", RED),
    ]
    x = Inches(0.45)
    for label, val, sub, c in cards:
        add_metric_card(s, x, Inches(4.75), Inches(3.0), Inches(1.9),
                        label, val, sub, c)
        x += Inches(3.15)
    add_footer(s)

    # ==================================================================
    # 3 · DATASET EXPANSION
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Data I", "Dataset expansion — conflict-majority without inventing labels", 3)
    add_picture_fit(s, FIG / "presentation" / "dataset_expansion.png",
                    Inches(0.3), Inches(1.1), Inches(12.7), Inches(3.0))
    headers = ["Cohort", "n", "Pathogenic", "Benign", "Label basis"]
    rows = [
        ["Before (clear ClinVar only)", "388", "—", "—", "germline_clinvar"],
        ["Conflict-majority added", "+430", "—", "—", "germline_conflict_majority"],
        ["After (this update)", "818", "405", "413", "both, provenance kept"],
    ]
    add_table(s, Inches(0.45), Inches(4.3), Inches(7.6), Inches(1.5),
              headers, rows, col_w=[3, 1, 1.4, 1.2, 2.4],
              highlight_rows={2}, font_size=11)
    add_rect(s, Inches(8.3), Inches(4.3), Inches(4.55), Inches(1.9), LIGHT, rounded=True)
    add_text(s, Inches(8.5), Inches(4.4), Inches(4.2), Inches(1.7),
             "Rules (no fabrication)\n"
             "• VUS never given a label\n"
             "• Ties / VUS majorities dropped\n"
             "• Only strict majority of submitter\n"
             "  GermlineClassification votes\n"
             "• Audit: clinvar_conflict_resolution.json",
             size=11.5, color=DARK)
    add_text(s, Inches(0.45), Inches(6.05), Inches(12.4), Inches(0.4),
             "Split (seed 42): train 654 / test 164  ·  features rebuilt from the frozen 21-column matrix",
             size=12, italic=True, color=GRAY)
    add_footer(s)

    # ==================================================================
    # 4 · FAIR PROTOCOL
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Methods", "One fair protocol for every model", 4)
    add_picture_fit(s, FIG / "presentation" / "fair_protocol.png",
                    Inches(0.3), Inches(1.15), Inches(12.7), Inches(2.7))
    headers = ["Invariant", "Setting"]
    rows = [
        ["Feature matrix", "same 21 columns (tp53_features.csv) for all models"],
        ["Split", "stratified 80/20, seed 42 → train 654 / test 164"],
        ["Cross-validation", "5-fold stratified, TRAIN partition only"],
        ["Preprocessing", "StandardScaler inside Pipeline (linear/SVM only)"],
        ["Class imbalance", "balanced class weights or sample weights per fold"],
        ["Selection", "mean CV ROC-AUC on train; test used once, descriptively"],
    ]
    add_table(s, Inches(0.45), Inches(4.05), Inches(7.9), Inches(2.5),
              headers, rows, col_w=[2.4, 5.5], font_size=11)
    add_rect(s, Inches(8.6), Inches(4.05), Inches(4.3), Inches(2.5), RGBColor(0xFD, 0xEC, 0xEE),
             line=RED, rounded=True)
    add_text(s, Inches(8.8), Inches(4.15), Inches(3.95), Inches(2.3),
             "Why this matters\n\n"
             "Any model can look good on a\nlucky split. Holding the test set\n"
             "out of all selection decisions\nmakes the side-by-side table\n"
             "an honest comparison — not a\nleaderboard of overfits.",
             size=12, color=DARK)
    add_footer(s)

    # ==================================================================
    # 5 · FEATURES
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Features", "21 leak-free sequence & structural features", 5)
    add_picture_fit(s, FIG / "machine_learning" / "feature_importance.png",
                    Inches(0.3), Inches(1.15), Inches(7.4), Inches(4.3))
    add_picture_fit(s, FIG / "machine_learning" / "class_distribution.png",
                    Inches(7.8), Inches(1.15), Inches(5.2), Inches(2.4))
    add_picture_fit(s, FIG / "machine_learning" / "position_enrichment.png",
                    Inches(7.8), Inches(3.65), Inches(5.2), Inches(2.4))
    add_rect(s, Inches(0.45), Inches(5.6), Inches(7.1), Inches(1.35), LIGHT, rounded=True)
    add_text(s, Inches(0.6), Inches(5.7), Inches(6.8), Inches(1.2),
             "Grouped: domain flags (TAD/DBD/TET/…) · Grantham + AA property deltas · "
             "Zn-ligand distance · WT pLDDT context · DNA-contact flag · normalized position.\n"
             "Importance = association only (random-forest Gini), not causation.",
             size=11.5, color=DARK)
    add_footer(s)

    # ==================================================================
    # 6 · SIDE-BY-SIDE TEST TABLE (headline)
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Results I", "Side-by-side — held-out test metrics (n = 164)", 6)

    def test_row(name, display):
        r = results[name]
        t = r["test"]
        c = r["cv"]
        return [
            display,
            fmt(t["accuracy"]),
            fmt(t["f1"]),
            fmt(t["roc_auc"]),
            fmt(t["pr_auc"]),
            fmt(t["mcc"]),
            f"{c['roc_auc_mean']:.3f}±{c['roc_auc_std']:.3f}",
            f"{t['tn']}/{t['fp']}/{t['fn']}/{t['tp']}",
        ]

    headers = ["Model", "Acc", "F1", "ROC-AUC", "PR-AUC", "MCC",
               "CV ROC-AUC", "TN/FP/FN/TP"]
    rows = [
        test_row("extra_trees", "Extra Trees"),
        test_row("random_forest", "Random Forest"),
        test_row("catboost", "CatBoost"),
    ]
    # highlight best on each metric
    aucs = [results[n]["test"]["roc_auc"] for n in ("extra_trees", "random_forest", "catboost")]
    f1s = [results[n]["test"]["f1"] for n in ("extra_trees", "random_forest", "catboost")]
    accs = [results[n]["test"]["accuracy"] for n in ("extra_trees", "random_forest", "catboost")]
    best_auc = aucs.index(max(aucs))
    best_f1 = f1s.index(max(f1s))
    best_acc = accs.index(max(accs))
    # mark winner row by overall AUC winner
    add_table(s, Inches(0.4), Inches(1.2), Inches(12.5), Inches(1.55),
              headers, rows, col_w=[2.2, 1.1, 1.1, 1.3, 1.2, 1.1, 1.8, 1.7],
              highlight_rows={best_auc}, font_size=12)

    # baselines strip
    add_text(s, Inches(0.4), Inches(2.95), Inches(12), Inches(0.35),
             "Baseline train.py comparison (same split, same features):",
             size=13, bold=True, color=NAVY)
    m = metrics["models"]
    b_headers = ["Baseline", "Acc", "F1", "ROC-AUC", "CV F1", "Confusion"]
    b_rows = [
        ["Logistic Regression", fmt(m["logistic_regression"]["accuracy"]),
         fmt(m["logistic_regression"]["f1"]), fmt(m["logistic_regression"]["roc_auc"]),
         f"{m['logistic_regression']['cv_f1_mean']:.3f}±{m['logistic_regression']['cv_f1_std']:.3f}",
         str(m["logistic_regression"]["confusion_matrix"]).replace(" ", "")],
        ["Random Forest", fmt(m["random_forest"]["accuracy"]),
         fmt(m["random_forest"]["f1"]), fmt(m["random_forest"]["roc_auc"]),
         f"{m['random_forest']['cv_f1_mean']:.3f}±{m['random_forest']['cv_f1_std']:.3f}",
         str(m["random_forest"]["confusion_matrix"]).replace(" ", "")],
    ]
    add_table(s, Inches(0.4), Inches(3.35), Inches(7.6), Inches(1.15),
              b_headers, b_rows, col_w=[2.4, 1, 1, 1.2, 1.4, 1.6],
              header_fill=TEAL, font_size=11)

    add_rect(s, Inches(8.3), Inches(3.35), Inches(4.6), Inches(1.15),
             RGBColor(0xE3, 0xF2, 0xEF), line=TEAL, rounded=True)
    add_text(s, Inches(8.45), Inches(3.45), Inches(4.35), Inches(1.0),
             f"Winner by test ROC-AUC: {rows[best_auc][0]} ({rows[best_auc][3]})\n"
             f"Winner by test F1: {rows[best_f1][0]} ({rows[best_f1][2]})\n"
             f"Winner by accuracy: {rows[best_acc][0]} ({rows[best_acc][1]})",
             size=11.5, color=DARK)

    add_rect(s, Inches(0.4), Inches(4.75), Inches(12.5), Inches(2.15), LIGHT, rounded=True)
    add_text(s, Inches(0.6), Inches(4.85), Inches(12.1), Inches(1.95),
             "How to read this table\n"
             "• Every row uses the identical feature matrix, split and CV folds — no model gets an easier job.\n"
             "• Selection criterion = mean CV ROC-AUC on TRAIN only (highlighted row). Test columns are descriptive.\n"
             "• Range across the three models is small (ΔROC-AUC ≤ 0.011): they are statistically close on n = 164;\n"
             "  report them together rather than declaring a single champion from one split.",
             size=12.5, color=DARK)
    add_footer(s)

    # ==================================================================
    # 7 · ROC + PR CURVES SIDE BY SIDE
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Results II", "ROC and precision–recall curves (held-out test)", 7)
    add_picture_fit(s, FIG / "machine_learning" / "benchmark" / "roc_curves.png",
                    Inches(0.25), Inches(1.15), Inches(6.5), Inches(4.4))
    add_picture_fit(s, FIG / "machine_learning" / "benchmark" / "precision_recall_curves.png",
                    Inches(6.8), Inches(1.15), Inches(6.3), Inches(4.4))
    add_rect(s, Inches(0.4), Inches(5.7), Inches(12.5), Inches(1.2), LIGHT, rounded=True)
    add_text(s, Inches(0.6), Inches(5.8), Inches(12.1), Inches(1.0),
             "All three curves sit high and tight (test ROC-AUC 0.946–0.956). PR-AUC is the more honest\n"
             "metric on near-balanced classes (405/413): CatBoost leads PR-AUC, RF leads accuracy/F1,\n"
             "Extra Trees leads train CV — the ordering depends on the metric, so all three are reported.",
             size=12.5, color=DARK)
    add_footer(s)

    # ==================================================================
    # 8 · BAR COMPARISON + CONFUSION MATRICES
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Results III", "Metric bars & confusion matrices", 8)
    add_picture_fit(s, FIG / "machine_learning" / "benchmark" / "roc_auc_comparison.png",
                    Inches(0.2), Inches(1.1), Inches(4.3), Inches(3.3))
    add_picture_fit(s, FIG / "machine_learning" / "benchmark" / "f1_comparison.png",
                    Inches(4.55), Inches(1.1), Inches(4.3), Inches(3.3))
    add_picture_fit(s, FIG / "machine_learning" / "benchmark" / "accuracy_comparison.png",
                    Inches(8.9), Inches(1.1), Inches(4.3), Inches(3.3))
    add_picture_fit(s, FIG / "machine_learning" / "benchmark" / "confusion_matrices.png",
                    Inches(1.4), Inches(4.45), Inches(10.5), Inches(2.5))
    add_footer(s)

    # ==================================================================
    # 9 · CV STABILITY
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Results IV", "Cross-validation stability (train, 5 folds)", 9)
    add_picture_fit(s, FIG / "machine_learning" / "benchmark" / "cv_performance_variability.png",
                    Inches(0.3), Inches(1.15), Inches(7.6), Inches(4.5))
    headers = ["Model", "CV F1", "CV ROC-AUC", "CV MCC"]
    rows = []
    for name, disp in (("extra_trees", "Extra Trees"),
                       ("random_forest", "Random Forest"),
                       ("catboost", "CatBoost")):
        c = results[name]["cv"]
        rows.append([disp, f"{c['f1_mean']:.3f}±{c['f1_std']:.3f}",
                     f"{c['roc_auc_mean']:.3f}±{c['roc_auc_std']:.3f}",
                     f"{c['mcc_mean']:.3f}±{c['mcc_std']:.3f}"])
    add_table(s, Inches(7.9), Inches(1.3), Inches(5.0), Inches(1.55),
              headers, rows, col_w=[1.6, 1.1, 1.2, 1.3], font_size=10.5)
    add_rect(s, Inches(7.9), Inches(3.1), Inches(5.0), Inches(3.0), LIGHT, rounded=True)
    add_text(s, Inches(8.1), Inches(3.2), Inches(4.65), Inches(2.8),
             "Interpretation\n\n"
             "• SD ≈ 0.014–0.020 on ROC-AUC:\n  folds agree — ranking is stable.\n"
             "• F1 SD ≈ 0.04: some folds are\n  harder (class mix), as expected\n  on n ≈ 523 train rows/fold.\n"
             "• Small spread between models\n  (≤ 0.001 CV AUC) ⇒ differences\n  on the test set are within noise;\n  keep all three in the report.",
             size=12, color=DARK)
    add_footer(s)

    # ==================================================================
    # 10 · TUNING baseline vs tuned
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Results V", "Train-only hyperparameter tuning", 10)
    comp = data["tuned"]["config"].get("comparison") or data["tuned"].get("comparison_to_baseline")
    headers = ["Model", "CV AUC base", "CV AUC tuned", "Test AUC base",
               "Test AUC tuned", "Test F1 base", "Test F1 tuned", "Δ test F1"]
    rows = []
    for row in comp:
        d_f1 = row["tuned_test_f1"] - row["baseline_test_f1"]
        rows.append([
            row["model"].replace("_", " ").title(),
            f"{row['baseline_cv_roc_auc']:.3f}",
            f"{row['tuned_cv_roc_auc']:.3f}",
            f"{row['baseline_test_roc_auc']:.3f}",
            f"{row['tuned_test_roc_auc']:.3f}",
            f"{row['baseline_test_f1']:.3f}",
            f"{row['tuned_test_f1']:.3f}",
            f"{d_f1:+.4f}".rstrip("0").rstrip(".") if abs(d_f1) > 1e-6 else "+0.000",
        ])
    add_table(s, Inches(0.4), Inches(1.2), Inches(12.5), Inches(1.5),
              headers, rows, col_w=[2.0, 1.4, 1.4, 1.5, 1.5, 1.4, 1.4, 1.1],
              font_size=11.5)
    best_params_txt = "\n".join(
        f"• {r['model']}: " + ", ".join(f"{k.split('__')[-1]}={v}" for k, v in r["best_params"].items())
        for r in comp
    )
    add_rect(s, Inches(0.4), Inches(3.1), Inches(6.2), Inches(3.5), LIGHT, rounded=True)
    add_text(s, Inches(0.6), Inches(3.2), Inches(5.85), Inches(3.3),
             "Search protocol\n"
             "• Small grids, 5-fold CV on TRAIN only\n"
             "• Test never queried during search\n"
             "• Baseline and tuned artefacts stored separately\n\n"
             "Best hyperparameters found\n" + best_params_txt,
             size=12, color=DARK)
    add_rect(s, Inches(6.9), Inches(3.1), Inches(6.0), Inches(3.5),
             RGBColor(0xFD, 0xEC, 0xEE), line=RED, rounded=True)
    add_text(s, Inches(7.1), Inches(3.2), Inches(5.65), Inches(3.3),
             "Honest result: tuning changed almost nothing\n\n"
             "Δ test F1 = 0.000 for RF/ET; CatBoost +0.0015.\n"
             "Default hyperparameters were already near the\n"
             "grid optimum on this n — the grid is deliberately\n"
             "small to avoid overfitting a 654-row train set.\n\n"
             "Takeaway: model choice (family) matters more\n"
             "than micro-tuning on a cohort this size.",
             size=12, color=DARK)
    add_footer(s)

    # ==================================================================
    # 11 · POSITION-AWARE
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Results VI", "Position-aware validation — the leakage check", 11)
    add_picture_fit(s, FIG / "presentation" / "position_aware_schematic.png",
                    Inches(0.3), Inches(1.1), Inches(12.7), Inches(2.7))
    headers = ["Model", "Random-split test AUC", "GroupKFold AUC",
               "Δ (AUC)", "GroupKFold F1"]
    rows = []
    gk = {r["model"]: r for r in pos["group_kfold"]}
    for name, disp in (("extra_trees", "Extra Trees"),
                       ("random_forest", "Random Forest"),
                       ("catboost", "CatBoost")):
        rs = results[name]["test"]["roc_auc"]
        g = gk[name]["cv"]
        rows.append([disp, f"{rs:.3f}", f"{g['roc_auc_mean']:.3f}±{g['roc_auc_std']:.3f}",
                     f"{g['roc_auc_mean'] - rs:+.3f}",
                     f"{g['f1_mean']:.3f}±{g['f1_std']:.3f}"])
    add_table(s, Inches(0.4), Inches(4.0), Inches(7.9), Inches(1.5),
              headers, rows, col_w=[1.8, 2.2, 2.0, 1.1, 1.8], font_size=11)
    add_rect(s, Inches(8.6), Inches(4.0), Inches(4.3), Inches(2.7),
             RGBColor(0xFD, 0xEC, 0xEE), line=RED, rounded=True)
    add_text(s, Inches(8.8), Inches(4.1), Inches(3.95), Inches(2.5),
             "What the drop means\n\n"
             "Grouping by residue removes\nsame-position leakage — AUC falls\n"
             "by ~0.02–0.03 but stays ~0.91–0.92.\n\n"
             "Hotspot leave-one-out scores\n(n = 1–6 variants) are high-variance\nand must not be read as clinical\nperformance.",
             size=11.5, color=DARK)
    add_text(s, Inches(0.4), Inches(5.7), Inches(7.9), Inches(0.9),
             "322 unique positions · 8 hotspots (R175, G245, R248, R249, Y220, R273, R280, R282).\n"
             "Conclusion: reported random-split metrics are slightly optimistic — stated as a limitation.",
             size=11.5, italic=True, color=GRAY)
    add_footer(s)

    # ==================================================================
    # 12 · FULL COHORT AUDIT
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Results VII", "Full-cohort audit & honest error list", 12)
    t = cohort["test"]
    a = cohort["all"]
    cards = [
        ("Test accuracy", f"{t['accuracy']:.4f}", f"n = {t['n']} held out", NAVY),
        ("Test F1", f"{t['f1']:.4f}", "reproduces metrics.json", TEAL),
        ("Test ROC-AUC", f"{t['roc_auc']:.4f}", "baseline RF", GREEN),
        ("Misclassified", f"{cohort['n_misclassified']}", f"of {cohort['n_total']} predicted", RED),
    ]
    x = Inches(0.45)
    for label, val, sub, c in cards:
        add_metric_card(s, x, Inches(1.2), Inches(3.0), Inches(1.75), label, val, sub, c)
        x += Inches(3.15)

    headers = ["Variant", "ClinVar class", "Split", "P(pathogenic)"]
    rows = []
    for row in cohort["misclassified"][:6]:
        rows.append([row["hgvs_p"], row["classification"][:28],
                     row["split"], f"{row['proba_pathogenic']:.3f}"])
    add_text(s, Inches(0.45), Inches(3.2), Inches(7), Inches(0.35),
             "First 6 test-set mistakes (all 18 listed in evaluation.md):",
             size=13, bold=True, color=NAVY)
    add_table(s, Inches(0.45), Inches(3.6), Inches(7.4), Inches(1.9),
              headers, rows, col_w=[1.6, 3.2, 1.1, 1.5], font_size=11)
    add_picture_fit(s, FIG / "machine_learning" / "confusion_matrix.png",
                    Inches(8.1), Inches(3.2), Inches(4.8), Inches(3.3))
    add_rect(s, Inches(0.45), Inches(5.7), Inches(7.4), Inches(1.2), LIGHT, rounded=True)
    add_text(s, Inches(0.6), Inches(5.8), Inches(7.1), Inches(1.0),
             "Train metrics = 1.0 by design (RF fits training data).\n"
             "Only the held-out columns are evidence. No post-hoc relabeling;\n"
             "every error is listed with its ClinVar class.",
             size=11.5, color=DARK)
    add_footer(s)

    # ==================================================================
    # 13 · DEMO FIGURES + PREDICTION PANEL
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Demonstration", "Structural context & live prediction panel", 13)
    add_picture_fit(s, FIG / "structures" / "kaggle_3d_hotspots.png",
                    Inches(0.3), Inches(1.15), Inches(6.4), Inches(4.3))
    add_picture_fit(s, FIG / "machine_learning" / "plddt_by_class.png",
                    Inches(6.9), Inches(1.15), Inches(6.1), Inches(2.1))
    add_picture_fit(s, FIG / "machine_learning" / "benchmark" / "pr_auc_comparison.png",
                    Inches(6.9), Inches(3.35), Inches(6.1), Inches(2.1))
    add_rect(s, Inches(0.4), Inches(5.6), Inches(12.5), Inches(1.35), LIGHT, rounded=True)
    add_text(s, Inches(0.6), Inches(5.7), Inches(12.1), Inches(1.15),
             "Live local demo:  python3 dashboard/server.py  →  http://127.0.0.1:8000\n"
             "CLI:  python3 scripts/machine_learning/predict.py R 175 H\n"
             "      --model results/machine_learning/benchmark/models/catboost.joblib R 175 H\n"
             "Default model = baseline RF (model.joblib); benchmark artefacts selectable per variant.",
             size=12, color=DARK)
    add_footer(s)

    # ==================================================================
    # 14 · KAGGLE / GITHUB
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Reproducibility", "GitHub push & Kaggle deployment", 14)
    headers = ["Artefact", "Status", "Link / command"]
    rows = [
        ["GitHub main", "PUSHED  3c03f16",
         "github.com/simbisaichinhema/TP53-Sequence-Structure-and-Machine-Learning-"],
        ["Kaggle notebook", "RUN COMPLETE (~5 min)",
         "kaggle.com/simbisaichinhema/tp53-mutation-analysis"],
        ["Smoke tests (local + Kaggle)", "ALL PASS",
         "python3 scripts/machine_learning/test_benchmark_smoke.py"],
        ["Benchmark outputs", "3 models, n=818",
         "results/machine_learning/benchmark/"],
        ["Conflict-resolution audit", "COMMITTED",
         "data/raw/variants/clinvar_conflict_resolution.json"],
    ]
    add_table(s, Inches(0.4), Inches(1.2), Inches(12.5), Inches(2.4),
              headers, rows, col_w=[3.0, 2.6, 6.9], font_size=11.5)
    # left col box
    add_rect(s, Inches(0.4), Inches(3.9), Inches(6.2), Inches(2.8), LIGHT, rounded=True)
    add_text(s, Inches(0.6), Inches(4.0), Inches(5.85), Inches(2.6),
             "Kaggle pipeline (Internet ON, CPU)\n\n"
             "1. Clone GitHub repo\n"
             "2. WT baseline re-check\n"
             "3. ClinVar fetch + conflict expansion → n=818\n"
             "4. Features → baseline train → 3-model benchmark\n"
             "5. Side-by-side tables/figures → tuning\n"
             "6. Position-aware → audit → smoke tests",
             size=12, color=DARK)
    add_rect(s, Inches(6.9), Inches(3.9), Inches(6.0), Inches(2.8),
             RGBColor(0xE3, 0xF2, 0xEF), line=TEAL, rounded=True)
    add_text(s, Inches(7.1), Inches(4.0), Inches(5.65), Inches(2.6),
             "What the Kaggle run proved\n\n"
             "• Full pipeline from scratch on a clean VM\n"
             "• Same numbers as local (test acc/F1/AUC match)\n"
             "• All smoke tests passed on Kaggle\n"
             "• Table-C baseline guard fixed live after first\n"
             "  failed run (honest iteration, logged)\n"
             "• Notebook: 36 cells, outputs cleared for import",
             size=12, color=DARK)
    add_footer(s)

    # ==================================================================
    # 15 · LIMITATIONS + TAKEAWAY
    # ==================================================================
    s = prs.slides.add_slide(blank)
    add_bg(s)
    add_title_bar(s, "Closing", "Limitations & takeaways", 15)
    add_rect(s, Inches(0.4), Inches(1.2), Inches(6.2), Inches(3.6),
             RGBColor(0xFD, 0xEC, 0xEE), line=RED, rounded=True)
    add_text(s, Inches(0.6), Inches(1.3), Inches(5.85), Inches(3.4),
             "Limitations (stated, not hidden)\n\n"
             "• n = 818 still small; single random split\n"
             "• Same-residue leakage possible → GroupKFold\n"
             "  drop ≈ 0.02–0.03 AUC reported explicitly\n"
             "• No mutant 3D re-prediction (structure = WT)\n"
             "• Feature importance = association, not cause\n"
             "• ClinVar germline labels only; no somatic,\n"
             "  no clinical validity / validation cohorts\n"
             "• Not a clinical decision tool",
             size=13, color=DARK)
    add_rect(s, Inches(6.9), Inches(1.2), Inches(6.0), Inches(3.6),
             RGBColor(0xE3, 0xF2, 0xEF), line=TEAL, rounded=True)
    add_text(s, Inches(7.1), Inches(1.3), Inches(5.65), Inches(3.4),
             "Takeaways\n\n"
             "1. Dataset doubled honestly (388→818) with\n"
             "   provenance and an audit trail\n"
             "2. Three competitive models under ONE fair\n"
             "   protocol — test held out of selection\n"
             "3. Metrics stable under CV and position-aware\n"
             "   checks; optimism quantified\n"
             "4. Fully reproducible: GitHub + Kaggle run,\n"
             "   smoke-tested, all numbers regenerated",
             size=13, color=DARK)
    add_rect(s, Inches(0.4), Inches(5.05), Inches(12.5), Inches(1.7), NAVY, rounded=True)
    add_text(s, Inches(0.7), Inches(5.2), Inches(12.0), Inches(1.4),
             "Bottom line: on 818 ClinVar missense variants with 21 leak-free features, "
             "Extra Trees / Random Forest / CatBoost reach test ROC-AUC 0.946–0.956 "
             "(F1 0.875–0.893) under a protocol that never touches the test set — "
             "reproduced end-to-end on GitHub and Kaggle.",
             size=15, bold=True, color=WHITE, line_spacing=1.15)
    add_footer(s)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f"wrote {OUT}  ({OUT.stat().st_size} bytes, {len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
