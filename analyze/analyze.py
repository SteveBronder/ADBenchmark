import io
import os
import matplotlib.pyplot as plt
import pandas as pd
from subprocess import check_output
import subprocess as subp
# Path definitions
figpath = '../docs/figs'
libpath = '../build/benchmark'
datapath = '../docs/data'

# List of library names
libs = ['fastad', 'stan', 'adept', 'baseline', 'cppad', 'sacado']

# List of test names
tests = ['log_sum_exp', 'matrix_product', 'normal_log_pdf', 'prod', 'prod_iter',
          'regression', 'stochastic_volatility', 'sum', 'sum_iter']

# Make plot font size bigger
plt.rcParams["font.size"] = "12"

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

# Run test for each library
def run(testname):
    df = pd.DataFrame()

    # save current working directory
    cur_path = os.getcwd()

    # run test for each lib and save times
    for lib in libs:

        # change directory to library
        # some libraries may require this to read configuration file
        path = os.path.join(lib_path(lib), lib + "_" + testname)
        print(path)

        # run and get output from each
        data_path = os.path.join("/tmp", str(testname + "_" + lib + "_multirun.csv"))
        exec_str = [path, "--benchmark_out_format=csv", "--benchmark_format=csv", "--benchmark_repetitions=30", "--benchmark_enable_random_interleaving=true ", "--benchmark_out=" + data_path]
        subp.run(exec_str, check=True)
        df_lib = pd.read_csv(data_path, sep=',', skiprows=8)
        # if ./doc/benchmark_aggs does not exist, create it
        multi_path = os.path.join(datapath, "benchmark_aggs")
        if not os.path.exists(multi_path):
          os.makedirs(multi_path)
        df_lib.to_csv(os.path.join(multi_path, str(testname + "_" + lib + ".csv")))
        df_lib.set_index('N', inplace=True)
        if lib == 'stan' and df_lib['name'].str.contains('varmat').any():
          df['stan'] = df_lib[df_lib['name'].str.contains('BM_stan<')]['cpu_time']
          df['stan_varmat'] = df_lib[df_lib['name'].str.contains('BM_stan_varmat')]['cpu_time']
        else:
          df[lib] = df_lib['cpu_time']

        # change back to current working directory
        os.chdir(cur_path)

    # save absolute time
    data_path = os.path.join(datapath, testname + "_multirun.csv")
    df.to_csv(data_path)

    # create relative time to fastad
    fastad_col = df['fastad'].copy()
    df = df.apply(lambda col: col / fastad_col)
    df.reset_index(level=df.index.names, inplace=True)

    return df

# For each test, run and plot
for test in tests:
    plot_test(run(test), test)
