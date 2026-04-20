#!/usr/bin/env python3
"""
Tiling Heatmap Generator
Usage: python tiling_heatmap.py <input.csv> [--metric wall_clock_s|user_cpu_s|sys_cpu_s|max_rss_kb]
"""

import argparse
import sys
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import FuncFormatter

def parse_defines(defines_str):
    """Extract W and H from define strings like 'W=8_H=8' or 'W=2048_H=2028'."""
    m = re.match(r'W=(\d+)_H=(\d+)', defines_str.strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None

def load_data(csv_path):
    df = pd.read_csv(csv_path)
    df['W'], df['H'] = zip(*df['defines'].apply(parse_defines))
    df = df.dropna(subset=['W', 'H'])
    df['W'] = df['W'].astype(int)
    df['H'] = df['H'].astype(int)
    return df

def build_heatmap(df, metric):
    # Average across reps
    agg = df.groupby(['W', 'H'])[metric].mean().reset_index()

    # Pivot to matrix: rows = H (sorted desc), cols = W (sorted asc)
    pivot = agg.pivot(index='H', columns='W', values=metric)
    pivot = pivot.sort_index(ascending=False)   # H descending on y-axis
    pivot = pivot.sort_index(axis=1, ascending=True)  # W ascending on x-axis
    return pivot

def make_label(metric):
    labels = {
        'wall_clock_s': 'Wall Clock Time (s)',
        'user_cpu_s':   'User CPU Time (s)',
        'sys_cpu_s':    'System CPU Time (s)',
        'max_rss_kb':   'Max RSS Memory (KB)',
    }
    return labels.get(metric, metric)

def plot_heatmap(pivot, metric, output_path):
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor('#0f0f14')
    ax.set_facecolor('#0f0f14')

    data = pivot.values
    vmin, vmax = np.nanmin(data), np.nanmax(data)

    # Custom colormap: deep navy → electric teal → hot amber
    cmap = mcolors.LinearSegmentedColormap.from_list(
        'perf',
        ['#0d1b2a', '#0e6e8c', '#00c9a7', '#f9c74f', '#f94144'],
        N=256
    )

    im = ax.imshow(data, aspect='auto', cmap=cmap, vmin=vmin, vmax=vmax,
                   interpolation='nearest')

    col_labels = [str(c) for c in pivot.columns]
    row_labels = [str(r) for r in pivot.index]

    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, color='#a0aec0', fontsize=9, fontfamily='monospace')
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, color='#a0aec0', fontsize=9, fontfamily='monospace')

    ax.set_xlabel('Tile Width (W)', color='#e2e8f0', fontsize=11, labelpad=10)
    ax.set_ylabel('Tile Height (H)', color='#e2e8f0', fontsize=11, labelpad=10)

    # Annotate cells
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            val = data[i, j]
            if not np.isnan(val):
                norm_val = (val - vmin) / (vmax - vmin) if vmax > vmin else 0.5
                text_color = '#ffffff' if norm_val < 0.6 else '#0d1b2a'
                ax.text(j, i, f'{val:.1f}', ha='center', va='center',
                        color=text_color, fontsize=8, fontfamily='monospace',
                        fontweight='bold')

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, pad=0.02, fraction=0.035)
    cbar.set_label(make_label(metric), color='#e2e8f0', fontsize=10, labelpad=10)
    cbar.ax.yaxis.set_tick_params(color='#a0aec0')
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#a0aec0', fontsize=8)
    cbar.outline.set_edgecolor('#2d3748')

    # Title
    ax.set_title(
        f'Tiling Performance Heatmap\n{make_label(metric)} — averaged over reps',
        color='#f7fafc', fontsize=13, fontweight='bold', pad=16,
        fontfamily='monospace'
    )

    # Spine styling
    for spine in ax.spines.values():
        spine.set_edgecolor('#2d3748')

    ax.tick_params(colors='#a0aec0', which='both')

    # Best/worst markers
    best_idx = np.unravel_index(np.nanargmin(data), data.shape)
    worst_idx = np.unravel_index(np.nanargmax(data), data.shape)

    for idx, marker, label in [(best_idx, '★', 'best'), (worst_idx, '▼', 'worst')]:
        ax.text(idx[1], idx[0] - 0.38, marker,
                ha='center', va='center', fontsize=11,
                color='#ffffff' if label == 'best' else '#ff6b6b')

    # Legend for markers
    ax.text(0.01, -0.09, '★ best   ▼ worst',
            transform=ax.transAxes, color='#a0aec0', fontsize=8,
            fontfamily='monospace')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    print(f"Saved heatmap to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate tiling performance heatmap from CSV.')
    parser.add_argument('csv', help='Input CSV file')
    parser.add_argument('--metric', default='wall_clock_s',
                        choices=['wall_clock_s', 'user_cpu_s', 'sys_cpu_s', 'max_rss_kb'],
                        help='Metric to visualise (default: wall_clock_s)')
    parser.add_argument('--output', default='heatmap.png', help='Output PNG file (default: heatmap.png)')
    args = parser.parse_args()

    df = load_data(args.csv)
    pivot = build_heatmap(df, args.metric)

    print(f"\nHeatmap grid ({args.metric}):")
    print(pivot.to_string())

    plot_heatmap(pivot, args.metric, args.output)

if __name__ == '__main__':
    main()
