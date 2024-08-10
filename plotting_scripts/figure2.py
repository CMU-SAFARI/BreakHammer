import seaborn as sns 
import matplotlib.pyplot as plt

from plot_setup import *

MAIN_PERF = "norm_weighted_speedup"
SHORT_NAME = "BH"
NUM_CORES = 4
MITIGATION_LIST = ["AQUA", "PARA", "TWiCe", "Graphene", "RFM", "Hydra", "REGA"]
BH_MITIGATION_LIST = [f"{mit}+{SHORT_NAME}" for mit in MITIGATION_LIST]
BH_MITIGATION_LIST = sorted(BH_MITIGATION_LIST + MITIGATION_LIST)

TRACE_COMBINATION_NAME = "microbenign"
TRACE_COMBINATION_FILE = f"{TRACE_COMBINATION_DIR}/{TRACE_COMBINATION_NAME}.mix"
CSV_DIR = f"{RESULT_DIR}/{TRACE_COMBINATION_NAME}/_csvs"

def plot_figure2(df):
    base_colors = sns.color_palette("pastel", int(len(MITIGATION_LIST)))
    dark_colors = [darken_color(color, 0.65) for color in base_colors]
    colors = base_colors + dark_colors
    colors[::2] = base_colors
    colors[1::2] = dark_colors

    mechanisms = ["Hydra", "RFM", "PARA", "AQUA", "BlockHammer"]
    df = df[df.configstr.isin(mechanisms)]

    fig, ax = plt.subplots(1,1, figsize=(6, 1.5))

    ax.grid(axis='y', linestyle='--', linewidth=0.5, color='gray', zorder=0)
    ax.grid(axis='x', linestyle='--', linewidth=0.5, color='gray', zorder=0)

    ax.set_axisbelow(True)

    sns.barplot(
        x='itRH', y=MAIN_PERF, 
        hue="configstr", 
        hue_order=mechanisms,
        data=df,
        palette="pastel",
        edgecolor='black', linewidth=1.05,
        errcolor="black", errwidth=1.05,
        ax=ax,
    )

    ax.set_xticklabels(['4K', '2K', '1K', '512', '256', '128', '64'])
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2])
    ax.set_xlabel("RowHammer Threshold $N_{RH}$")
    ax.axhline(y=1, color='black', linestyle='--', linewidth=1)
    ax.set_ylim([0, 1.2])

    ax.set_ylabel('Normalized\nWeighted Speedup')

    ax.legend(loc='center', ncols=5, fontsize=10, bbox_to_anchor=(0.45, 1.25))

    fig.savefig(f'{PLOT_DIR}/figure2.pdf', bbox_inches='tight')

if __name__ == "__main__":
    df = general_df_setup(CSV_DIR, TRACE_DIR, TRACE_COMBINATION_FILE, NUM_CORES)
    plot_figure2(df)