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

def plot_figure12(df):
    colors = sns.color_palette("pastel", int(len(BH_MITIGATION_LIST)))

    FONT_SIZE = 10
    plt.rcParams.update({'font.size': FONT_SIZE})

    fig, ax = plt.subplots(1,1, figsize=(6, 1.5))

    plot_df = df[(df.tRH > 0)].copy()

    # print(plot_df)


    plot_df["itRH"] = 1 / plot_df["tRH"]

    hue_order = BH_MITIGATION_LIST
    ax.grid(axis='y', linestyle='--', linewidth=0.5, color='gray', zorder=0)
    ax.grid(axis='x', linestyle='--', linewidth=0.5, color='gray', zorder=0)
    ax.set_axisbelow(True)

    sns.barplot(
        x='itRH', 
        y=MAIN_PERF, 
        hue="configstr",
        hue_order=hue_order,
        data=plot_df,
        ax=ax, 
        palette=colors,
        edgecolor='black', linewidth=1.05,
        errcolor="black", errwidth=0.9,
    )

    ax.set_xticklabels([f"{int(x)}" for x in reversed(sorted(plot_df.tRH.unique()))])

    ax.axhline(1, color='black', linestyle='--', linewidth=1)
    ax.set_ylabel('Normalized\nWeighted Speedup')
    ax.set_xlabel('RowHammer Threshold ($N_{RH}$)')
    ax.legend(loc='center',  ncol=4, fancybox=True, shadow=False, handletextpad=0.5, columnspacing=0.75, bbox_to_anchor=(0.5, 1.30), fontsize=FONT_SIZE)
    Y_LIM = 1.15
    ticks, tick_labels = get_ticks_and_labels(Y_LIM, 0.025)
    ax.set_yticks(ticks)
    ax.set_yticklabels(tick_labels)
    ax.set_ylim([0.90, Y_LIM])

    fig.savefig(f'{PLOT_DIR}/figure12.pdf', bbox_inches='tight')

if __name__ == "__main__":
    df = general_df_setup(CSV_DIR, TRACE_DIR, TRACE_COMBINATION_FILE, NUM_CORES)
    plot_figure12(df)