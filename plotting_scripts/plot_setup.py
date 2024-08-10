import os
import argparse
import warnings
import pandas as pd
import colorsys
from pandas.errors import SettingWithCopyWarning
from scipy.stats import gmean

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)
warnings.simplefilter(action='ignore', category=SettingWithCopyWarning)

argparser = argparse.ArgumentParser(
    prog="RunPersonal",
    description="Run ramulator2 simulations on a personal computer"
)

argparser.add_argument("-wd", "--working_directory")
argparser.add_argument("-tc", "--trace_combination")
argparser.add_argument("-td", "--trace_directory")
argparser.add_argument("-rd", "--result_directory")

args = argparser.parse_args()

WORK_DIR = args.working_directory
TRACE_COMBINATION_DIR = args.trace_combination
TRACE_DIR = args.trace_directory
RESULT_DIR = args.result_directory
PLOT_DIR = f"{RESULT_DIR}/_plots"

if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)

def general_df_setup(csv_dir, trace_dir, trace_comb_file, num_cores):
    def get_path(name):
        return f"{csv_dir}/{name}"

    mpkidf = pd.read_csv(f"{trace_dir}/mpki.csv")
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
        for i in range(num_cores): 
            cnts[row[f"label_core{i}"]] += 1
        label = ""
        for category in ["H", "M", "L", "A"]:
            for i in range(cnts[category]):
                label += category
        row["label"] = label
        return row 

    core_list = [f"core{i}" for i in range(num_cores)]
    df = pd.read_csv(get_path('merged.csv'))
    name_list = ["trace", "w"] + core_list
    wldf = pd.read_csv(trace_comb_file, sep=',', header=None, names=name_list)

    for i in range(num_cores):
        mpkidf[f"core{i}"] = mpkidf["benchmark"]

    df = df.merge(wldf, on='trace', how='left')
    df["label"] = "Unknown"
    df["MPKI"] = 0
    for i in range(num_cores):
        df = df.merge(mpkidf[[f"core{i}", "label", "MPKI"]], on=f'core{i}', how='left', suffixes=('', f'_core{i}'))

    df["MPKI"] = 0
    for i in range(num_cores):
        df["MPKI"] += df[f"MPKI_core{i}"]
    df = df.apply(lambda row: label_touch(row), axis=1)

    df["mitigation"] = df["mitigation"].replace({"Dummy": "No Mitigation", "TWiCe-Ideal": "TWiCe"})
    base_df = df[df.thresh_type == "NONE"]
    bh_df = df[df.thresh_type == "MEAN"]
    merg_df = bh_df.merge(base_df, on=["mitigation", "tRH", "trace"], how="left", suffixes=('', '_merg'))
    merg_df["norm_bh_speedup"] = merg_df["norm_weighted_speedup"] / merg_df["norm_weighted_speedup_merg"]
    merg_df["norm_bh_energy"] = merg_df["norm_energy"] / merg_df["norm_energy_merg"]
    base_df["norm_bh_speedup"] = 1
    base_df["norm_bh_energy"] = 1
    base_df["norm_max_slowdown"] = 1
    merg_df["norm_max_slowdown"] = merg_df["max_slowdown"] / merg_df["max_slowdown_merg"]
    merg_df = merg_df[merg_df.columns.drop(list(merg_df.filter(regex='_merg')))]
    df = pd.concat([base_df, merg_df], ignore_index=True)

    df["thresh_type"] = df["thresh_type"].replace({"NONE": "", "MEAN": f"+BH"})
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
            "norm_energy": gmean(subdf["norm_energy"]),
            "norm_bh_energy": gmean(subdf["norm_bh_energy"])
        })

    gdf = pd.DataFrame(gmeans)

    df = pd.concat([df[['label', 'configstr', 'tRH', 'MPKI', 'norm_weighted_speedup', "norm_bh_speedup", "norm_energy", "norm_bh_energy", "norm_max_slowdown"]], gdf], ignore_index=True)
    df = df[["label", "norm_weighted_speedup", "norm_bh_speedup", "configstr", "norm_energy", "norm_bh_energy", "norm_max_slowdown", "tRH"]].groupby(["label", "configstr","tRH"]).mean().reset_index()
    df["itRH"] = 1 / df["tRH"]

    return df

def darken_color(color, amount=0.25):
    normalized_color = [x / 255.0 if x > 1 else x for x in color]
    c = colorsys.rgb_to_hls(*normalized_color)
    new_lightness = max(0, min(1, amount * c[1]))
    darkened_color = colorsys.hls_to_rgb(c[0], new_lightness, c[2])
    darkened_color = [max(0, min(1, x)) for x in darkened_color]
    return darkened_color

def get_ticks_and_labels(lim_cap, step):
    range_cap = int(lim_cap / step) + 1
    ticks = [i * step for i in range(range_cap)]
    tick_labels = [f"{i * step:.2f}" if i % 2 == 0 else "" for i in range(range_cap)]
    return ticks, tick_labels