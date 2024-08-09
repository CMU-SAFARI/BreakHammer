import pandas as pd 
import seaborn as sns 
import matplotlib.pyplot as plt
import colorsys

from plot_setup import *

MAIN_PERF = "norm_weighted_speedup"
SHORT_NAME = "BH"
NUM_CORES = 4
MITIGATION_LIST = ["AQUA", "PARA", "TWiCe", "Graphene", "RFM", "Hydra", "REGA"]
BH_MITIGATION_LIST = [f"{mit}+{SHORT_NAME}" for mit in MITIGATION_LIST]
BH_MITIGATION_LIST = sorted(BH_MITIGATION_LIST + MITIGATION_LIST)

def darken_color(color, amount=0.25):
    normalized_color = [x / 255.0 if x > 1 else x for x in color]
    c = colorsys.rgb_to_hls(*normalized_color)
    new_lightness = max(0, min(1, amount * c[1]))
    darkened_color = colorsys.hls_to_rgb(c[0], new_lightness, c[2])
    darkened_color = [max(0, min(1, x)) for x in darkened_color]
    return darkened_color

base_colors = sns.color_palette("pastel", int(len(MITIGATION_LIST)))
dark_colors = [darken_color(color, 0.65) for color in base_colors]
colors = base_colors + dark_colors
colors[::2] = base_colors
colors[1::2] = dark_colors

TRACE_COMBINATION_NAME = "microattack"
TRACE_COMBINATION_FILE = f"{TRACE_COMBINATION_DIR}/{TRACE_COMBINATION_NAME}.mix"
CSV_DIR = f"{RESULT_DIR}/{TRACE_COMBINATION_NAME}/_csvs"

def get_path(name):
    return f"{CSV_DIR}/{name}"

def get_ticks_and_labels(lim_cap, step):
    range_cap = int(lim_cap / step) + 1
    ticks = [i * step for i in range(range_cap)]
    tick_labels = [f"{i * step:.2f}" if i % 2 == 0 else "" for i in range(range_cap)]
    return ticks, tick_labels

df = pd.read_csv(get_path('multicore.csv'))
df["mitigative_action_cnt"] = df["VRR"] + df["RFM"] + df["RRS_reswap"] + df["RRS_unswap"] + df["RRS_swap"] +\
                              df["AQUA_migrate"] + df["AQUA_r_migrate"]
df["mitigation"] = df["mitigation"].replace({"Dummy": "No Mitigation", "TWiCe-Ideal": "TWiCe"})
df["thresh_type"] = df["thresh_type"].replace({"NONE": "", "MEAN": f"+{SHORT_NAME}"})
df["configstr"] = df["mitigation"] + df["thresh_type"]

dfs = []
for mitigation, mdf in df.groupby("mitigation"):
    mitdf = mdf.copy()
    basedf = mdf[(mdf.tRH == 4096) & (mdf.thresh_type != f"+{SHORT_NAME}")].copy()
    mitdf = mitdf.merge(basedf[["trace", "mitigative_action_cnt"]], on="trace", how="inner", suffixes=('', '_base'))
    mitdf["norm_mitigative_action_cnt"] = mitdf["mitigative_action_cnt"] / mitdf["mitigative_action_cnt_base"]
    dfs.append(mitdf[mitdf.norm_mitigative_action_cnt > 0])
    
df = pd.concat(dfs)
df[["tRH", "trace", "norm_mitigative_action_cnt", "configstr"]]
df[df["configstr"].str.contains("RRS")]

num_mitigations = df.mitigation.nunique()

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
        hue_order=[mitigation, f"{mitigation}+{SHORT_NAME}"],
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