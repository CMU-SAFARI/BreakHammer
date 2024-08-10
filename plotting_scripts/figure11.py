import pandas as pd 
import seaborn as sns 
import matplotlib.pyplot as plt
from scipy.stats import gmean

from plot_setup import *

MAIN_PERF = "norm_bh_speedup"
NUM_CORES = 4
SHORT_NAME = "BH"
MITIGATION_LIST = ["AQUA", "PARA", "TWiCe", "Graphene", "RFM", "Hydra", "REGA"]
BH_MITIGATION_LIST = [f"{mit}+{SHORT_NAME}" for mit in MITIGATION_LIST]

TRACE_COMBINATION_NAME = "microbenign"
TRACE_COMBINATION_FILE = f"{TRACE_COMBINATION_DIR}/{TRACE_COMBINATION_NAME}.mix"
CSV_DIR = f"{RESULT_DIR}/{TRACE_COMBINATION_NAME}/_csvs"

def plot_figure11(df):
    colors = sns.color_palette("pastel", int(len(BH_MITIGATION_LIST)))

    fig, ax = plt.subplots(1,1, figsize=(6, 1.5))
    tRH = 1024

    ax.add_artist(plt.Rectangle((5.5, 0), 6, 60, fill=True, edgecolor="black", facecolor='#e5e5e5', linewidth=1, linestyle='-',  zorder=0))
    ax.grid(axis='y', linestyle='--', linewidth=0.5, color='gray', zorder=0)

    ax.set_axisbelow(True)

    ax = sns.barplot(
        x='label',
        y=MAIN_PERF,
        hue="configstr", 
        data=df[df.tRH == tRH],
        palette=colors,
        edgecolor='black', linewidth=1.05,
        errcolor="black", errwidth=1.05,
        hue_order=BH_MITIGATION_LIST,
    )

    handles, labels = ax.get_legend_handles_labels()

    hue_order = BH_MITIGATION_LIST
    num_bars_per_group = len(hue_order)
    sorted_bars = sorted(ax.patches, key=lambda x: x.get_x())
    nrh_grp_lookup = sorted(df["tRH"].unique(), reverse=True)

    bar_idx = 0
    for i, bar in enumerate(sorted_bars):
        if bar.get_width() == 0 and bar.get_height() == 0:
            continue
        mit_idx = bar_idx % num_bars_per_group
        mit_grp = bar_idx // num_bars_per_group
        mit_name = hue_order[mit_idx]
        mit_bits = 0
        mit_trh = nrh_grp_lookup[mit_grp]
        bar_val = bar.get_height() 

    ax.axhline(1, color='black', linestyle='--', linewidth=1)
    ax.set_ylabel("Normalized\nWeighted Speedup")
    ax.set_xlabel('Benchmarks')
    ax.legend(loc='center',  ncol=4, fancybox=True, shadow=False, handletextpad=0.5, columnspacing=0.75, bbox_to_anchor=(0.5, 1.30), fontsize=10)

    Y_LIM = 1.05
    ticks, tick_labels = get_ticks_and_labels(Y_LIM, 0.025)
    ax.set_yticks(ticks)
    ax.set_yticklabels(tick_labels)
    ax.set_ylim([0.90, Y_LIM])

    fig.savefig(f'{PLOT_DIR}/figure11.pdf', bbox_inches='tight')

if __name__ == "__main__":
    df = general_df_setup(CSV_DIR, TRACE_DIR, TRACE_COMBINATION_FILE, NUM_CORES)
    plot_figure11(df)