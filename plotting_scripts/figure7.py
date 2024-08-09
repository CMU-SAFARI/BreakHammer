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

colors = sns.color_palette("pastel", int(len(BH_MITIGATION_LIST)))

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

mpkidf = pd.read_csv(f"{TRACE_DIR}/mpki.csv")
mpkidf = mpkidf[mpkidf.benchmark != 'gups']

mpkidf = mpkidf.sort_values(by=['MPKI'], ascending=[False])
hi_mpkidf = mpkidf[mpkidf.MPKI > 60].copy()
mi_mpkidf = mpkidf[(mpkidf.MPKI > 10) & (mpkidf.MPKI < 60)].copy()
lo_mpkidf = mpkidf[mpkidf.MPKI < 10].copy()

hi_mpkidf["label"] = "H"
mi_mpkidf["label"] = "M"
lo_mpkidf["label"] = "L"

attackers = ["atk1.trace", "atkrfm.trace", "atkrfm2.trace", "atkrfm8K.trace"]
mpkidf = pd.concat([hi_mpkidf, mi_mpkidf, lo_mpkidf, pd.DataFrame({
    "benchmark": attackers,
    "label": ["A"] * len(attackers),
    "MPKI":[0] * len(attackers)
})])

def label_touch(row):
    cnts = {"H":0, "M":0, "L":0, "A":0}
    for i in range(NUM_CORES): 
        cnts[row[f"label_core{i}"]] += 1
    label = ""
    for category in ["H", "M", "L", "A"]:
        for i in range(cnts[category]):
            label += category
    row["label"] = label
    return row 

core_list = [f"core{i}" for i in range(NUM_CORES)]
df = pd.read_csv(get_path('merged.csv'))
name_list = ["trace", "w"] + core_list
wldf = pd.read_csv(TRACE_COMBINATION_FILE, sep=',', header=None, names=name_list)

max_tsars = -1
max_base = -1
for mitigation in MITIGATION_LIST:
    check_df = df.copy()
    mit_df = check_df[check_df.mitigation == mitigation]
    base_df = mit_df[mit_df.thresh_type == "NONE"]
    sars_df = mit_df[mit_df.thresh_type == "MEAN"]
    merg_df = sars_df.merge(base_df, on=["mitigation", "tRH", "trace"], how="left", suffixes=('', '_merg'))

for i in range(NUM_CORES):
    mpkidf[f"core{i}"] = mpkidf["benchmark"]

df = df[df.mitigation != "BlockHammer"]
df = df.merge(wldf, on='trace', how='left')
df["label"] = "Unknown"
df["MPKI"] = 0
for i in range(NUM_CORES):
    df = df.merge(mpkidf[[f"core{i}", "label", "MPKI"]], on=f'core{i}', how='left', suffixes=('', f'_core{i}'))

df["MPKI"] = 0
for i in range(NUM_CORES):
    df["MPKI"] += df[f"MPKI_core{i}"]
df = df.apply(lambda row: label_touch(row), axis=1)

df["mitigation"] = df["mitigation"].replace({"Dummy": "No Mitigation", "TWiCe-Ideal": "TWiCe"})
base_df = df[df.thresh_type == "NONE"]
bh_df = df[df.thresh_type == "MEAN"]
merg_df = bh_df.merge(base_df, on=["mitigation", "tRH", "trace"], how="left", suffixes=('', '_merg'))
merg_df["norm_bh_speedup"] = merg_df["norm_weighted_speedup"] / merg_df["norm_weighted_speedup_merg"]
base_df["norm_bh_speedup"] = 1
base_df["norm_max_slowdown"] = 1
merg_df["norm_max_slowdown"] = merg_df["max_slowdown"] / merg_df["max_slowdown_merg"]
merg_df = merg_df[merg_df.columns.drop(list(merg_df.filter(regex='_merg')))]
df = pd.concat([base_df, merg_df], ignore_index=True)

df["thresh_type"] = df["thresh_type"].replace({"NONE": "", "MEAN": f"+{SHORT_NAME}"})
df["configstr"] = df["mitigation"] + df["thresh_type"]

df[core_list + ["label", "MPKI"]].sort_values(by=["MPKI"], ascending=[False])

df = df.sort_values(by="MPKI", ascending=False)

gmeans = []
for (configstr, tRH), subdf in df.groupby(['configstr', 'tRH']):
    gmeans.append({
        'label': 'geomean',
        'MPKI': subdf.MPKI.mean(),
        'configstr': configstr,
        'tRH': tRH,
        'norm_weighted_speedup': gmean(subdf["norm_weighted_speedup"]),
        'norm_bh_speedup': gmean(subdf["norm_bh_speedup"]),
        "norm_energy": gmean(subdf["norm_energy"])
    })

gdf = pd.DataFrame(gmeans)

df = pd.concat([df[['label', 'configstr', 'tRH', 'MPKI', 'norm_weighted_speedup', "norm_bh_speedup", "norm_energy", "norm_max_slowdown"]], gdf], ignore_index=True)
df = df[["label", "norm_weighted_speedup", "norm_bh_speedup", "configstr", "norm_energy", "norm_max_slowdown", "tRH"]].groupby(["label", "configstr","tRH"]).mean().reset_index()

fig, ax = plt.subplots(1,1, figsize=(6, 1.5))
tRH = 1024

ax.add_artist(plt.Rectangle((5.5, 0), 6, 50, fill=True, edgecolor="black", facecolor='#e5e5e5', linewidth=1, linestyle='-',  zorder=0))
# draw gray gridlines behind the bars
ax.grid(axis='y', linestyle='--', linewidth=0.5, color='gray', zorder=0)

# move gridlines behind the bars
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

Y_LIM = 3.5
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
    # if bar_val > Y_LIM:
    #     anno = ax.annotate(f"{bar_val:2.1f}x", (bar.get_x() - 0.08, Y_LIM - 0.08), xytext=(-17, -17), weight='bold',\
    #         arrowprops=dict(color=bar.get_facecolor(), shrink=0.05, width=1, headwidth=3, headlength=3),\
    #         textcoords='offset points', ha='center', va='bottom', fontsize=10, color=bar.get_facecolor())
    #     anno.set_path_effects([path_effects.Stroke(linewidth=1, foreground='black'),
    #                          path_effects.Normal()])
    #     arrow = anno.arrow_patch
    #     arrow.set_path_effects([path_effects.Stroke(linewidth=2, foreground='black'),
    #                          path_effects.Normal()])
    bar_idx += 1

ax.axhline(1, color='black', linestyle='--', linewidth=1)
ax.set_ylabel("Normalized\nWeighted Speedup")
ax.set_xlabel('Benchmarks')
ax.legend(loc='center',  ncol=4, fancybox=True, shadow=False, handletextpad=0.5, columnspacing=0.75, bbox_to_anchor=(0.5, 1.25), fontsize=10)

ticks, tick_labels = get_ticks_and_labels(Y_LIM, 0.25)
ax.set_yticks(ticks)
ax.set_yticklabels(tick_labels)
ax.set_ylim([0, Y_LIM])

fig.savefig(f'{PLOT_DIR}/figure7.pdf', bbox_inches='tight')