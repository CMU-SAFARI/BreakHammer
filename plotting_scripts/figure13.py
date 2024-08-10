import pandas as pd 
import seaborn as sns 
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches

from plot_setup import *

MAIN_PERF = "norm_bh_speedup"
NUM_CORES = 4
SHORT_NAME = "BH"
MITIGATION_LIST = ["AQUA", "PARA", "TWiCe", "Graphene", "RFM", "Hydra", "REGA"]
BH_MITIGATION_LIST = [f"{mit}+{SHORT_NAME}" for mit in MITIGATION_LIST]

colors = sns.color_palette("pastel", int(len(BH_MITIGATION_LIST)))

TRACE_COMBINATION_NAME = "microbenign"
TRACE_COMBINATION_FILE = f"{TRACE_COMBINATION_DIR}/{TRACE_COMBINATION_NAME}.mix"
CSV_DIR = f"{RESULT_DIR}/{TRACE_COMBINATION_NAME}/_csvs"

def plot_figure13(csv_dir):
    def get_path(name):
        return f"{csv_dir}/{name}"

    PLOT_NRH = 64
    NS_PER_CYCLE = 0.234
    SHORT_NAME = "BH"

    df = pd.read_csv(get_path("multicore_mem.csv"))
    df = df[(df.mitigation != "BlockHammer")]
    df = df[(df.tRH == PLOT_NRH) | (df.mitigation == "Dummy")]
    df["_mitigation"] = df["mitigation"].copy()
    df["_mitigation"] = df["_mitigation"].replace({"Dummy": "Baseline", "TWiCe-Ideal": "TWiCe"})
    df["_thresh_type"] = df["thresh_type"].copy()
    df["_thresh_type"] = df["_thresh_type"].replace({"NONE": "", "MEAN": f"+{SHORT_NAME}"})
    df["configstr"] = df["_mitigation"] + df["_thresh_type"]
    df["pN_val"] = df["pN_val"] * NS_PER_CYCLE

    mitigations = list(set(df.mitigation.unique()) - set(["Dummy", "TWiCe-Ideal"])) + ["TWiCe"]
    num_mechs = len(mitigations)

    fig = plt.figure(figsize=(6, 2.5))
    spec = fig.add_gridspec(2, 8)

    colors = sns.color_palette("pastel", 3)
    plot_id = 0
    for mech in ["Hydra", "Graphene", "REGA", "RFM", "AQUA", "TWiCe", "PARA"]:
        plot_df = df[(df["configstr"].str.contains(mech)) | (df["mitigation"] == "Dummy")]
        if mech == "XDDDD":
            ax_row = None
            ax_col = None
            ax = fig.add_subplot(spec[:, 3])
        else:
            ax_row = int(plot_id / 4) 
            ax_col = plot_id % 4
            col_begin = 2*ax_col + ax_row
            col_end = 2*ax_col + ax_row + 2
            ax = fig.add_subplot(spec[ax_row, col_begin:col_end])
            plot_id += 1

        grouped_df = plot_df.groupby(['pN_key', 'configstr'])['pN_val'].mean().reset_index()

        y1 = grouped_df[(grouped_df['configstr'] == mech)]['pN_val'].values
        y2 = grouped_df[(grouped_df['configstr'] == f"{mech}+{SHORT_NAME}")]['pN_val'].values
        x = grouped_df['pN_key'].unique()

        hue_order = [mech, f"{mech}+{SHORT_NAME}", "Baseline"]

        sns.lineplot(data=plot_df, x="pN_key", y="pN_val", hue="configstr",
                    hue_order=hue_order, palette=colors, ax=ax, linewidth=2, errorbar=('ci', 0))

        lines = ax.get_lines()
        legend_texts = ax.get_legend().get_texts()

        for line, label in zip(lines, ax.get_legend().get_texts()):
            if label.get_text() == "Baseline":
                line.set_linestyle("--")
                line.set_linewidth(1.5)
                line.set_color("black")

        if ax_col != None and ax_col > 0:
            ax.set_yticklabels([])

        start = None
        current_better = None
        fill_colors = [colors[0], colors[1]]
        p_alpha = 0.15

        for i in range(len(x)):
            better = 'y1' if y1[i] < y2[i] else 'y2'
            if better != current_better:
                if start is not None:
                    ax.axvspan(x[start], x[i], color=fill_colors[0] if current_better == 'y1' else fill_colors[1], alpha=p_alpha)
                start = i
            current_better = better

        if start is not None:
            ax.axvspan(x[start], x[-1], color=fill_colors[0] if current_better == 'y1' else fill_colors[1], alpha=p_alpha)
        
        ax.grid(which="major", axis="y", color="black", alpha=0.5, linestyle="dotted", linewidth=0.5, zorder=0)
        ax.grid(which="minor", axis="y", color="gray", alpha=0.2, linestyle="dotted", linewidth=0.5, zorder=0)
        ax.axhline(y=1, color="black", linestyle="dashed", linewidth=0.5, zorder=0)

        custom_entry = mlines.Line2D([], [], color='black', linestyle='--', linewidth=2.5, label='Baseline')

        handles, labels = ax.get_legend_handles_labels()
        handles = [h for h, l in zip(handles, labels) if l != "Baseline"]
        labels = [l for l in labels if l != "Baseline"]

        handles.extend([custom_entry]) 
        labels.extend(['Baseline']) 

        legend_loc = "upper left" 
        ax.legend(loc=legend_loc, handles=handles, labels=labels, prop={'size': 7}, frameon=True, handlelength=0.5, handletextpad=0.5, columnspacing=0.5, ncols=1)

        if mech == "AQUA":
            lims = [0, 3000]
            ticks = [0, lims[1]//2, lims[1]]
            ax.set_ylim(lims)
            ax.set_yticks(ticks, ticks)
        else:
            ax.set_ylim([0, 500])
            ax.set_yticks([0, 250, 500], [0, 250, 500])
        ax.set_ylabel("")
        ax.set_xlabel("")
        ax.set_title("")

    ax_group = fig.add_subplot(spec[:, :])
    ax_group.set_xticks([])
    ax_group.set_yticks([])
    ax_group.set_frame_on(False)
    ax_group.set_ylabel("Memory Latency (ns)", labelpad=30)
    ax_group.set_xlabel("Request Percentile ($P_{N}$)", labelpad=20)
    plt.subplots_adjust(hspace=0.40, wspace=1.50)

    fig.savefig(f'{PLOT_DIR}/figure13.pdf', bbox_inches='tight')

if __name__ == "__main__":
    plot_figure13(CSV_DIR)