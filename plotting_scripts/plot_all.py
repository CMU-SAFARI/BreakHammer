from figure2 import plot_figure2
from figure7 import plot_figure7
from figure8 import plot_figure8
from figure9 import plot_figure9
from figure10 import plot_figure10
from figure11 import plot_figure11
from figure12 import plot_figure12
from figure13 import plot_figure13

from plot_setup import *

def plot_all_figures():
    print(f"[INFO] Reading attacker data")
    atk_df = general_df_setup(f"{RESULT_DIR}/microattack/_csvs", TRACE_DIR, f"{TRACE_COMBINATION_DIR}/microattack.mix", 4)
    print(f"[INFO] Reading benign data")
    ben_df = general_df_setup(f"{RESULT_DIR}/microbenign/_csvs", TRACE_DIR, f"{TRACE_COMBINATION_DIR}/microbenign.mix", 4)

    print(f"[INFO] Generating Figure2")
    plot_figure2(ben_df.copy())
    print(f"[INFO] Generated Figure2 to {PLOT_DIR}/figure2.pdf")
    print(f"[INFO] Generating Figure7")
    plot_figure7(atk_df.copy())
    print(f"[INFO] Generated Figure7 to {PLOT_DIR}/figure7.pdf")
    print(f"[INFO] Generating Figure8")
    plot_figure8(atk_df.copy())
    print(f"[INFO] Generated Figure8 to {PLOT_DIR}/figure8.pdf")
    print(f"[INFO] Generating Figure9")
    plot_figure9(f"{RESULT_DIR}/microattack/_csvs")
    print(f"[INFO] Generated Figure9 to {PLOT_DIR}/figure9.pdf")
    print(f"[INFO] Generating Figure10")
    plot_figure10(atk_df.copy())
    print(f"[INFO] Generated Figure10 to {PLOT_DIR}/figure10.pdf")
    print(f"[INFO] Generating Figure11")
    plot_figure11(ben_df.copy())
    print(f"[INFO] Generated Figure11 to {PLOT_DIR}/figure11.pdf")
    print(f"[INFO] Generating Figure12")
    plot_figure12(ben_df.copy())
    print(f"[INFO] Generated Figure12 to {PLOT_DIR}/figure12.pdf")
    print(f"[INFO] Generating Figure13 (This might take a while, e.g., >3 mins)")
    plot_figure13(f"{RESULT_DIR}/microbenign/_csvs")
    print(f"[INFO] Generated Figure13 to {PLOT_DIR}/figure13.pdf")

if __name__ == "__main__":
    plot_all_figures()