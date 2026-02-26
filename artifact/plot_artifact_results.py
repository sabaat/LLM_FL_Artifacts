#!/usr/bin/env python3
"""
Read success.txt from each SAM's SPM folders (strength 1 and strength 4).
Produces: results summary (with mutation strength 4 section and comparison) and 4 graphs:
  1. Initial accuracy drop with SPM (strength 1 only, per SAM).
  2. Effect of mutation strength (1 vs 4) per SAM, all 5 SPMs.
  3. Mutation types (all 5 SPMs) with strength 1 vs 4 aggregated over SAMs.
  4. Windowed results: cumulative matches/mismatches by code-position window (0-25%, 25-50%, 50-75%, 75-100%).
"""
import json
import os
import sys

# 4 SAMs and 5 SPMs (must match run_artifact.sh)
SAMS = ["BooleanLogic", "MisplacedReturn", "OffByOne", "OperatorSwap"]
SPMS = ["commented", "variable", "dead_code", "variable_cumulative", "dead_code_cumulative"]
SPM_LABELS = ["commented", "variable", "dead_code", "var_cumul", "dead_cumul"]
WINDOW_LABELS = ["0-25%", "25-50%", "50-75%", "75-100%"]


def read_success_count(folder: str) -> int:
    path = os.path.join(folder, "success.txt")
    if not os.path.isfile(path):
        return 0
    with open(path, "r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def count_first_n(artifact_dir: str, sam: str, n: int) -> int:
    first_n_dir = os.path.join(artifact_dir, f"first{n}_{sam}")
    if not os.path.isdir(first_n_dir):
        return 0
    return sum(1 for f in os.listdir(first_n_dir) if f.lower().endswith(".json"))


def collect_windowed_results(artifact_dir: str):
    """Aggregate windowed_results.json from all spm_* and spm_*_strength4/<spm> folders. Returns (matches_per_window, mismatches_per_window) as lists for 0-25, 25-50, 50-75, 75-100, or (None, None) if none found."""
    windows = ["0-25", "25-50", "50-75", "75-100"]
    agg_m = {w: 0 for w in windows}
    agg_mm = {w: 0 for w in windows}
    found = False
    for sam in SAMS:
        for base_name in [f"spm_{sam}", f"spm_{sam}_strength4"]:
            base = os.path.join(artifact_dir, base_name)
            if not os.path.isdir(base):
                continue
            for spm in SPMS:
                path = os.path.join(base, spm, "windowed_results.json")
                if not os.path.isfile(path):
                    continue
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for w in windows:
                        agg_m[w] += data.get("matches", {}).get(w, 0)
                        agg_mm[w] += data.get("mismatches", {}).get(w, 0)
                    found = True
                except Exception:
                    pass
    if not found:
        return None, None
    return [agg_m[w] for w in windows], [agg_mm[w] for w in windows]


def main():
    artifact_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    n_per_sam_default = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    # Collect strength 1: sam -> spm -> count
    results = {}
    results_strength4 = {}
    n_per_sam = {}
    for sam in SAMS:
        spm_base = os.path.join(artifact_dir, f"spm_{sam}")
        spm_base_4 = os.path.join(artifact_dir, f"spm_{sam}_strength4")
        if not os.path.isdir(spm_base):
            continue
        n_per_sam[sam] = count_first_n(artifact_dir, sam, n_per_sam_default) or n_per_sam_default
        results[sam] = {}
        for spm in SPMS:
            results[sam][spm] = read_success_count(os.path.join(spm_base, spm))
        results_strength4[sam] = {}
        if os.path.isdir(spm_base_4):
            for spm in SPMS:
                results_strength4[sam][spm] = read_success_count(os.path.join(spm_base_4, spm))
        else:
            for spm in SPMS:
                results_strength4[sam][spm] = 0

    if not results:
        print("No SAM results found under artifact_dir. Run run_artifact.sh first.")
        return

    # Summary file: strength 1, strength 4, and comparison
    summary_path = os.path.join(artifact_dir, "results_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(
            "For each SAM: out of N programs where the LLM successfully localized the fault,\n"
            "how many were still localized after each SPM?\n\n"
        )
        f.write("=" * 80 + "\n\n")
        f.write("Mutation strength 1\n")
        f.write("-" * 40 + "\n")
        for sam in SAMS:
            if sam not in results:
                continue
            n = n_per_sam.get(sam, n_per_sam_default)
            f.write(f"SAM: {sam} (N = {n})\n")
            for spm in SPMS:
                c = results[sam].get(spm, 0)
                f.write(f"  SPM ({spm:22s}): {c:2d} / {n}\n")
            f.write("\n")
        f.write("=" * 80 + "\n\n")
        f.write("Mutation strength 4 (comparison)\n")
        f.write("-" * 40 + "\n")
        for sam in SAMS:
            if sam not in results_strength4:
                continue
            n = n_per_sam.get(sam, n_per_sam_default)
            f.write(f"SAM: {sam} (N = {n})\n")
            for spm in SPMS:
                c = results_strength4[sam].get(spm, 0)
                f.write(f"  SPM ({spm:22s}): {c:2d} / {n}\n")
            f.write("\n")
        f.write("=" * 80 + "\n\n")
        f.write("Comparison: strength 1 vs 4 (still localized)\n")
        f.write("-" * 40 + "\n")
        for sam in SAMS:
            if sam not in results:
                continue
            n = n_per_sam.get(sam, n_per_sam_default)
            f.write(f"SAM: {sam} (N = {n})\n")
            for spm in SPMS:
                c1 = results[sam].get(spm, 0)
                c4 = results_strength4.get(sam, {}).get(spm, 0)
                f.write(f"  SPM ({spm:22s}): strength1={c1:2d}  strength4={c4:2d}\n")
            f.write("\n")
    win_m, win_mm = collect_windowed_results(artifact_dir)
    if win_m is not None and win_mm is not None:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("=" * 80 + "\n\n")
            f.write("Windowed results (cumulative over all test_llm runs)\n")
            f.write("-" * 40 + "\n")
            for i, w in enumerate(WINDOW_LABELS):
                f.write(f"  Window {w}: Matches = {win_m[i]}, Mismatches = {win_mm[i]}\n")
            f.write("\n")
    print(f"Summary written to {summary_path}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib not available; skipping graphs.")
        return

    sams_found = [s for s in SAMS if s in results]
    if not sams_found:
        return
    max_n = max(n_per_sam.get(s, n_per_sam_default) for s in sams_found)
    has_strength4 = any(os.path.isdir(os.path.join(artifact_dir, f"spm_{s}_strength4")) for s in sams_found)

    x = np.arange(len(sams_found))
    width = 0.15
    multipliers = [-2, -1, 0, 1, 2]
    colors = ["#4CAF50", "#81C784", "#A5D6A7", "#C8E6C9", "#2E7D32"]

    # ---- Graph 1: Initial accuracy drop with SPM (strength 1 only) ----
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    for i, spm in enumerate(SPMS):
        counts = [results[sam].get(spm, 0) for sam in sams_found]
        offset = width * multipliers[i]
        bars = ax1.bar(x + offset, counts, width, label=SPM_LABELS[i], color=colors[i], edgecolor="black", linewidth=0.5)
        for b, c in zip(bars, counts):
            ax1.annotate(str(c), xy=(b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=8)
    ax1.set_ylabel("Still localized (count)")
    ax1.set_xlabel("SAM (bug type)")
    ax1.set_title("Graph 1: Initial accuracy drop with SPM (mutation strength 1)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(sams_found, rotation=15, ha="right")
    ax1.legend(loc="upper right", fontsize=8)
    ax1.set_ylim(0, max_n + 1)
    ax1.axhline(y=max_n, color="gray", linestyle="--", alpha=0.5)
    plt.tight_layout()
    out1 = os.path.join(artifact_dir, "artifact_results.png")
    plt.savefig(out1, dpi=150)
    plt.close()
    print(f"Graph 1 saved to {out1}")

    if not has_strength4:
        print("No strength-4 data found; skipping graphs 2 and 3.")
        # Still plot Graph 4 (windowed) if we have data, then exit.
        if win_m is not None and win_mm is not None:
            fig4, ax4 = plt.subplots(figsize=(8, 5))
            x4 = np.arange(len(WINDOW_LABELS))
            w4 = 0.35
            bars_m = ax4.bar(x4 - w4 / 2, win_m, w4, label="Matches", color="#4CAF50", edgecolor="black", linewidth=0.5)
            bars_mm = ax4.bar(x4 + w4 / 2, win_mm, w4, label="Mismatches", color="#E53935", edgecolor="black", linewidth=0.5)
            for b in bars_m:
                if b.get_height() > 0:
                    ax4.annotate(str(int(b.get_height())), xy=(b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=9)
            for b in bars_mm:
                if b.get_height() > 0:
                    ax4.annotate(str(int(b.get_height())), xy=(b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=9)
            ax4.set_ylabel("Count (cumulative)")
            ax4.set_xlabel("Code position (line number %)")
            ax4.set_title("Graph 4: Windowed results — matches vs mismatches by code position")
            ax4.set_xticks(x4)
            ax4.set_xticklabels(WINDOW_LABELS)
            ax4.legend()
            ax4.set_ylim(0, max(max(win_m + win_mm) + 2, 1))
            plt.tight_layout()
            out4 = os.path.join(artifact_dir, "artifact_results_windowed.png")
            plt.savefig(out4, dpi=150)
            plt.close()
            print(f"Graph 4 saved to {out4}")
        else:
            print("No windowed_results.json found; skipping graph 4.")
        return

    # ---- Graph 2: Effect of mutation strength (1 vs 4) per SAM, all 5 SPMs ----
    # Per SAM: 5 SPMs × 2 strengths = 10 bars
    fig2, ax2 = plt.subplots(figsize=(14, 6))
    n_spms = len(SPMS)
    bar_w = 0.04
    for i, spm in enumerate(SPMS):
        for j, strength in enumerate([1, 4]):
            if strength == 1:
                counts = [results[sam].get(spm, 0) for sam in sams_found]
                label = f"{SPM_LABELS[i]} (str 1)"
                color = colors[i]
            else:
                counts = [results_strength4.get(sam, {}).get(spm, 0) for sam in sams_found]
                label = f"{SPM_LABELS[i]} (str 4)"
                import matplotlib.colors as mcolors
                rgb = mcolors.to_rgb(colors[i])
                color = mcolors.to_hex([max(0, c - 0.25) for c in rgb])
            offset = (i * 2 + j) * 0.05 - 0.45
            bars = ax2.bar(x + offset, counts, bar_w, label=label, color=color, edgecolor="black", linewidth=0.3)
            for b, c in zip(bars, counts):
                ax2.annotate(str(c), xy=(b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=7)
    ax2.set_ylabel("Still localized (count)")
    ax2.set_xlabel("SAM (bug type)")
    ax2.set_title("Graph 2: Effect of mutation strength (1 vs 4) per SAM, all 5 SPMs")
    ax2.set_xticks(x)
    ax2.set_xticklabels(sams_found, rotation=15, ha="right")
    ax2.legend(loc="upper right", fontsize=7, ncol=2)
    ax2.set_ylim(0, max_n + 1)
    plt.tight_layout()
    out2 = os.path.join(artifact_dir, "artifact_results_strength_comparison.png")
    plt.savefig(out2, dpi=150)
    plt.close()
    print(f"Graph 2 saved to {out2}")

    # ---- Graph 3: Mutation types (all 5 SPMs), strength 1 vs 4 aggregated over SAMs ----
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    x3 = np.arange(len(SPMS))
    w = 0.35
    sum_s1 = [sum(results.get(sam, {}).get(spm, 0) for sam in sams_found) for spm in SPMS]
    sum_s4 = [sum(results_strength4.get(sam, {}).get(spm, 0) for sam in sams_found) for spm in SPMS]
    bars1 = ax3.bar(x3 - w / 2, sum_s1, w, label="Strength 1", color="#4CAF50", edgecolor="black", linewidth=0.5)
    bars4 = ax3.bar(x3 + w / 2, sum_s4, w, label="Strength 4", color="#1976D2", edgecolor="black", linewidth=0.5)
    for b in bars1:
        ax3.annotate(str(int(b.get_height())), xy=(b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=9)
    for b in bars4:
        ax3.annotate(str(int(b.get_height())), xy=(b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=9)
    ax3.set_ylabel("Still localized (count, summed over SAMs)")
    ax3.set_xlabel("SPM (mutation type)")
    ax3.set_title("Graph 3: Mutation types (all 5 SPMs) — strength 1 vs 4")
    ax3.set_xticks(x3)
    ax3.set_xticklabels(SPM_LABELS, rotation=15, ha="right")
    ax3.legend()
    ax3.set_ylim(0, max(max(sum_s1 + sum_s4) + 2, 1))
    plt.tight_layout()
    out3 = os.path.join(artifact_dir, "artifact_results_mutation_types.png")
    plt.savefig(out3, dpi=150)
    plt.close()
    print(f"Graph 3 saved to {out3}")

    # ---- Graph 4: Windowed results (cumulative) ----
    if win_m is not None and win_mm is not None:
        fig4, ax4 = plt.subplots(figsize=(8, 5))
        x4 = np.arange(len(WINDOW_LABELS))
        w4 = 0.35
        bars_m = ax4.bar(x4 - w4 / 2, win_m, w4, label="Matches", color="#4CAF50", edgecolor="black", linewidth=0.5)
        bars_mm = ax4.bar(x4 + w4 / 2, win_mm, w4, label="Mismatches", color="#E53935", edgecolor="black", linewidth=0.5)
        for b in bars_m:
            if b.get_height() > 0:
                ax4.annotate(str(int(b.get_height())), xy=(b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=9)
        for b in bars_mm:
            if b.get_height() > 0:
                ax4.annotate(str(int(b.get_height())), xy=(b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=9)
        ax4.set_ylabel("Count (cumulative)")
        ax4.set_xlabel("Code position (line number %)")
        ax4.set_title("Graph 4: Windowed results — matches vs mismatches by code position")
        ax4.set_xticks(x4)
        ax4.set_xticklabels(WINDOW_LABELS)
        ax4.legend()
        ax4.set_ylim(0, max(max(win_m + win_mm) + 2, 1))
        plt.tight_layout()
        out4 = os.path.join(artifact_dir, "artifact_results_windowed.png")
        plt.savefig(out4, dpi=150)
        plt.close()
        print(f"Graph 4 saved to {out4}")
    else:
        print("No windowed_results.json found; skipping graph 4.")


if __name__ == "__main__":
    main()
