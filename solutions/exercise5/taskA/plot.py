#!/usr/bin/env python3
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd


METRICS = [
    ("wall_clock_s", "Wall Clock (s)"),
    ("user_cpu_s",   "User CPU (s)"),
    ("sys_cpu_s",    "Sys CPU (s)"),
    ("max_rss_kb",   "Max RSS (KB)"),
]

def format_defines(raw_define: str) -> str:
    for s in raw_define.split("_"):
        if "FLAGS=" in s:
            return s.removeprefix("FLAGS=")
    return ""
        

def plot(input_file_name: str):
    input_df = pd.read_csv(input_file_name)
    result = input_df.groupby(['defines', 'args'], dropna=False)['wall_clock_s'].agg(['mean', 'std']).reset_index()
    result['label'] = result.apply(
        lambda row: format_defines(row['defines']), 
        axis=1
    )
    result = result.sort_values(by='mean', ascending=False)
    
    plt.figure(figsize=(12, 7))
    plt.bar(result['label'], result['mean'], yerr=result['std'], capsize=5, color='skyblue', edgecolor='navy')
    plt.ylabel("Wall Clock Time (s)")
    plt.title(Path(input_file_name).stem)
    plt.tight_layout()
    
    plt.savefig(f"{Path(input_file_name).stem}.png", dpi=300)
    plt.close()




def main():
    csv_files = list(Path('.').glob('*.csv'))
    if not csv_files:
        print("No CSV files found in the current directory.")
        return

    for csv_file in csv_files:
        try:
            plot(str(csv_file))
        except Exception as e:
            print(f"  Error plotting {csv_file}: {e}")


if __name__ == "__main__":
    main()