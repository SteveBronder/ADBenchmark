import io
import os
import matplotlib.pyplot as plt
import pandas as pd
from subprocess import check_output
import subprocess as subp
import cpu_info as cpu_i
import hashlib
from datetime import datetime
import sys
import shutil
# Path definitions
current_directory_name = os.path.split(os.getcwd())[1]
if (current_directory_name == "analyze"):
  figpath = '../docs/figs'
  libpath = '../build/benchmark'
  datapath = '../docs/data'
else:
  figpath = './docs/figs'
  libpath = './build/benchmark'
  datapath = './docs/data'


# List of library names
libs = ['fastad', 'stan', 'adept', 'baseline', 'cppad', 'sacado']

# List of test names
tests = ['log_sum_exp', 'matrix_product', 'normal_log_pdf', 'prod', 'prod_iter',
          'regression', 'stochastic_volatility', 'sum', 'sum_iter']
tests = ['regression']
# Make plot font size bigger
plt.rcParams["font.size"] = "12"

CPU_LIST = "4"        # e.g. "2" or "0,2,4" or "0-3"

# Creates path to test for lib
def lib_path(libname):
    return os.path.join(libpath, libname)

def bin_name(libname, testname):
    return ''.join([libname, '_', testname])

# Plot result of test
def plot_test(df, name):
    axes = df.plot(x='N',
                   kind='line',
                   marker='.',
                   xticks=df['N'],
                   xlabel='N (input size)',
                   ylabel='Avg Time / FastAD Avg Time',
                   title=name,
                   figsize=(8,6))
    axes.set_xscale('log', base=2)
    axes.set_yscale('log', base=2)
    plt.savefig(os.path.join(figpath, name + '_fig.png'))


def is_numactl_available():
    """
    Checks if the 'numactl' command is available in the system's PATH.

    Returns:
        bool: True if 'numactl' is found, False otherwise.
    """
    return shutil.which("numactl") is not None

# Run test for each library
def run(testname, results_path, args):
    # run test for each lib and save times
    print("---------\n", testname, "\n---------")
    for lib in libs:
        print("___________\n", lib, "\n___________")
        # change directory to library
        # some libraries may require this to read configuration file
        path = os.path.join(lib_path(lib), lib + "_" + testname)
        # run and get output from each
        data_path = os.path.join(results_path, str(testname + "_" + lib + "_multirun.csv"))
        if is_numactl_available():
           base_exec = ["numactl", "--physcpubind=" + args.cpu, "--membind=" + args.membind]
        else:
           base_exec = []
        exec_str = base_exec + [path, "--benchmark_out_format=csv", "--benchmark_format=csv", "--benchmark_repetitions=30", "--benchmark_enable_random_interleaving=true ", "--benchmark_out=" + data_path]
        print("Running: ", ' '.join(exec_str))
        subp.run(exec_str, check=True)
    return None

def parse_args():
    import argparse
    ap = argparse.ArgumentParser(description="Generate a human-readable benchmark system report (Linux).")
    ap.add_argument("--short", action="store_true", help="Print only the top summary.")
    ap.add_argument("--json", action="store_false", help="Also print JSON after the human-readable report.")
    ap.add_argument("--no-color", action="store_false", help="Disable ANSI colors.")
    ap.add_argument("--cpu", default=CPU_LIST, help="If numactl available, comma-separated list of CPU cores to use (default: %(default)s).")
    ap.add_argument("--membind", default=str(0), help="If numactl available, integer of NUMA node CPU is on (default: %(default)s).")
    ap.add_argument("--results-path", default=datapath, help="Path to save results (default: %(default)s).")
    ap.add_argument("--file_base", default="", help="Base name for output files (default: hash of cpu info + datetime). ")
    return ap.parse_args()

# For each test, run and plot


def main():
  for test in tests:
    args = parse_args()
    text, js = cpu_i.build_report(args)
    encoded_text = text.encode('utf-8')
    # Hash for performance report folder
    base_file_name = args.file_base
    if (base_file_name == ""):
        base_file_name = hashlib.sha256(encoded_text).hexdigest()
    print(text)
    formatted_datetime = datetime.now().strftime("%Y_%m_%d_H%H_M%M_S%S")
    multi_path = os.path.join(datapath, "benchmarks" + formatted_datetime + "_" + base_file_name)
    # Make multi path folder if does not exist
    if not os.path.exists(multi_path):
        os.makedirs(multi_path)
    # Write text to readme.md in multi_path
    with open(os.path.join(multi_path, "README.md"), "w") as f:
        f.write(text)
    run(test, multi_path, args)

if __name__ == "__main__":
    main()
