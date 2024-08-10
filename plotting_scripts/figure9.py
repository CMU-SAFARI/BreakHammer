import pandas as pd 
import seaborn as sns 
import matplotlib.pyplot as plt

from plot_setup import *

def plot_figure9(csv_dir):
    def get_path(name):
        return f"{csv_dir}/{name}"

    df = pd.read_csv(get_path('multicore.csv'))
    df["mitigative_action_cnt"] = df["VRR"] + df["RFM"] + df["RRS_reswap"] + df["RRS_unswap"] + df["RRS_swap"] +\
                                df["AQUA_migrate"] + df["AQUA_r_migrate"]
    df["mitigation"] = df["mitigation"].replace({"Dummy": "No Mitigation", "TWiCe-Ideal": "TWiCe"})
    df["thresh_type"] = df["thresh_type"].replace({"NONE": "", "MEAN": f"+BH"})
    df["configstr"] = df["mitigation"] + df["thresh_type"]

    dfs = []
    for mitigation, mdf in df.groupby("mitigation"):
        mitdf = mdf.copy()
        basedf = mdf[(mdf.tRH == 4096) & (mdf.thresh_type != f"+BH")].copy()
        mitdf = mitdf.merge(basedf[["trace", "mitigative_action_cnt"]], on="trace", how="inner", suffixes=('', '_base'))
        mitdf["norm_mitigative_action_cnt"] = mitdf["mitigative_action_cnt"] / mitdf["mitigative_action_cnt_base"]
        # mitdf.to_csv(f"mitcheck_{mitigation}.csv")
        dfs.append(mitdf[mitdf.norm_mitigative_action_cnt > 0])
        
    df = pd.concat(dfs)
    df[["tRH", "trace", "norm_mitigative_action_cnt", "configstr"]]
    df[df["configstr"].str.contains("RRS")]

    DIM_X = 3
    DIM_Y = 2
    TITLE_FONT_SZ = 12

    fig, axarr = plt.subplots(DIM_Y, DIM_X, figsize=(8.0, 3.0), sharey=False, sharex=True)
    fig.text(0.04, 0.5, 'Normalized\nPreventive Actions',\
                va='center', ha='center', rotation='vertical', fontsize=TITLE_FONT_SZ)

    colors = sns.color_palette("pastel", 2)
    colors = [darken_color(color, 0.75) for color in colors]

    for i, (mitigation, mdf) in enumerate(df.groupby("mitigation")):
        ax = axarr.flatten()[i]
        row_idx = i // DIM_X
        col_idx = i % DIM_X
        ax.grid(axis='y', linestyle='--', linewidth=0.5, color='gray', zorder=0)
        ax.grid(axis='x', linestyle='--', linewidth=0.5, color='gray', zorder=0)
        ax.set_axisbelow(True)
        
        ci = 100
        if mitigation == "AQUA":
            ci = 75
        
        sns.lineplot(
            data=mdf,
            x='tRH',
            y='norm_mitigative_action_cnt',
            hue="configstr",
            hue_order=[mitigation, f"{mitigation}+BH"],
            errorbar=("ci", ci),
            n_boot=len(mdf.index),
            ax=ax,
            palette=colors,
        )
        
        ax.set_xscale('log')
        ax.set_xticks(sorted(df.tRH.unique()))
        ax.set_xticks([], minor=True)
        ax.set_xticklabels([str(x) if x < 1024 else str(int(x/1024))+"K" for x in sorted(df.tRH.unique())])
        ax.set_xlim([4096, 64])

        ax.set_ylabel('')
        if row_idx == DIM_Y - 1 and col_idx == DIM_X // 2:
            ax.set_xlabel('RowHammer Threshold ($N_{RH}$)', fontsize=TITLE_FONT_SZ)
        else:
            ax.set_xlabel('')
        
        if mitigation in ["AQUA"]:
            lim = [0, 30]
            ticks = [1, lim[1]//2, lim[1]]
            ax.set_yticks(ticks)
            ax.set_yticklabels([f"{tick}" for tick in ticks])
            ax.set_ylim(lim)
        elif mitigation in ["PARA"]:
            lim = [0, 40]
            ticks = [1, lim[1]//2, lim[1]]
            ax.set_yticks(ticks)
            ax.set_yticklabels([f"{tick}" for tick in ticks])
            ax.set_ylim(lim)
        elif mitigation in ["RFM"]:
            lim = [0, 20]
            ticks = [1, lim[1]//2, lim[1]]
            ax.set_yticks(ticks)
            ax.set_yticklabels([f"{tick}" for tick in ticks])
            ax.set_ylim(lim)
        else:
            ax.set_yticks([1, 25, 50, 75, 100])
            ax.set_yticklabels(["1", "", "50", "", "100"])
            ax.set_ylim([0, 100])
            
        ax.legend(loc='upper left', ncol=1, fancybox=True, shadow=False, handletextpad=0.5, columnspacing=0.75, fontsize=8) #bbox_to_anchor=(-0.25, 1.02),
        
    plt.tight_layout(rect=[0.05, -0.05, 1, 1], w_pad=0)

    fig.savefig(f'{PLOT_DIR}/figure9.pdf', bbox_inches='tight')

if __name__ == "__main__":
    plot_figure9(f"{RESULT_DIR}/microbenign/_csvs")