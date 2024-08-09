import os
import argparse
import warnings
from pandas.errors import SettingWithCopyWarning
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
PLOT_DIR = f"{WORK_DIR}/plots"

if not os.path.exists(PLOT_DIR):
    os.makedirs(PLOT_DIR)