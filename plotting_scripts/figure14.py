import pandas as pd 
import seaborn as sns 
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches

from plot_setup import *

TRACE_COMBINATION_NAME = "microattack"
TRACE_COMBINATION_FILE = f"{TRACE_COMBINATION_DIR}/{TRACE_COMBINATION_NAME}.mix"
CSV_DIR = f"{RESULT_DIR}/{TRACE_COMBINATION_NAME}/_csvs"

def plot_figure14(csv_dir):
    def get_path(name):
        return f"{csv_dir}/{name}"

    metric = "weighted_speedup"

    df = pd.read_csv(get_path('merged.csv'))
    df["mitigation"] = df["mitigation"].replace({"Dummy": "No Mitigation", "TWiCe-Ideal": "TWiCe"})
    df["thresh_type"] = df["thresh_type"].replace({"NONE": "", "MEAN": f"+BH"})
    df["configstr"] = df["mitigation"] + df["thresh_type"]
    df["itRH"] = 1 / df["tRH"]

    df = df[df.mitigation.isin(["BlockHammer", "AQUA", "PARA", "RFM"])]

    fig, ax = plt.subplots(1,1, figsize=(6, 1.5))

    ax.grid(axis='y', linestyle='--', linewidth=0.5, color='gray', zorder=0)
    ax.grid(axis='x', linestyle='--', linewidth=0.5, color='gray', zorder=0)

    ax.set_axisbelow(True)

    sns.barplot(
        x='itRH', y="norm_"+metric, 
        hue="configstr", 
        hue_order=[f"PARA+BH", f"AQUA+BH", f"RFM+BH", "BlockHammer"],
        data=df,
        palette="pastel",
        edgecolor='black', linewidth=1.05,
        errcolor="black", errwidth=1.05,
        ax=ax,
    )

    ax.set_xticklabels(['4K', '2K', '1K', '512', '256', '128', '64'])
    ax.set_xlabel("RowHammer Threshold $N_{RH}$")
    ax.axhline(y=1, color='black', linestyle='--', linewidth=1)

    ax.set_ylabel('Normalized\nWeighted Speedup')

    ax.legend(loc='center', ncols=4, fontsize=10, bbox_to_anchor=(0.5, 1.25))

    fig.savefig(f'{PLOT_DIR}/figure14.pdf', bbox_inches='tight')

if __name__ == "__main__":
    plot_figure14(CSV_DIR)