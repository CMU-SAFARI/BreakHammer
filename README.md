## BreakHammer: Enhancing RowHammer Mitigations by Carefully Throttling Suspect Threads
BreakHammer is a technique that reduces the performance overhead of RowHammer mitigation mechanisms by carefully reducing the number of performed RowHammer-preventive actions without compromising system robustness. Described in the MICRO 2024 paper: https://arxiv.org/abs/2404.13477.

## Repository File Structure 

```
.
+-- ae_results/                     # Simulation results and plots (will be overwritten when new experiments are executed)
+-- cputraces/                      # CPU traces for 56 single-core workloads
+-- mixes/                          # Workload mixes
|   +-- microattack.mix/            # 51 workloads of varying memory intensities with an attacker present 
|   +-- microbenign.mix/            # 51 bening-only workloads
+-- plotting_scripts/               # Scripts to use extracted simulation statistics and create the plots in our paper
+-- scripts/                        # Scripts to post-process raw data and extract statistics for plotting
+-- src/                            # Ramulator2 source code
|   +-- dram_controller/
|   |   +--impl/plugin
|   |   |  +-- throttler.cpp        # Ramulator2 plugin that implements main BreakHammer functionality
|   ...
...
+-- README.md                       # This file
```

## Installation Guide:

### Prerequisites:
- Git
- g++ with c++20 capabilities (g++-10 or above recommended)
- Python3 (3.10 or above recommended)
- Podman (Optional)
  - We have tested Podman 4.5.1 on Ubuntu 22.04.1
 
### Installation steps:
1. Clone the repository `git clone https://github.com/CMU-SAFARI/BreakHammer.git`
2. Install python dependencies, build Ramulator2, and download traces with `./run_simple_test.sh`[^1]

[^1]: To start (or stop) using Podman, the repository should be rebuilt using `./run_simple_test.sh` with (or without) `podman run`

## Example Use
1. Run Ramulator2 simulations `./run_with_slurm.sh` or `./run_with_slurm_podman.sh`[^2]. If you do not have Slurm use `./run_with_personalcomputer.sh` instead
2. Wait for the simulations to finish. You can use `./check_run_status.sh` to track simulation progress for multicore and singlecore runs (this script also creates intermediate scripts that can restart failed runs)
3. Parse simulation results and collects statistics with `./parse_results.sh`
4. Generate figures with `./plot_all_figures.sh`

[^2]: `./run_with_slurm_podman.sh` can be executed *without* using Podman since the script launches Slurm jobs that *use* Podman.

## Simulation Configuration Parameters
Execution of Ramulator2 simulations can be configured with the following configuration parameters. These parameters reside in `scripts/run_config.py` unless the parameter description below states a different path.

`PERSONAL_RUN_THREADS`: Number of parallel threads used to launch simulations with `./run_with_personalcomputer.sh`

`SLURM_USERNAME`: Slurm username. Defaults to `$USER`

`MAX_SLURM_JOBS`: Maximum number of Slurm jobs submitted by the user allowed at any time

`SLURM_SUBMIT_DELAY`: Delay between submitting Slurm jobs (until job limit is reached)

`SLURM_RETRY_DELAY`: Delay between retrying to submit Slurm jobs (when job limit is reached)

`AE_SLURM_PART_NAME`: Job partition of the submitted Slurm jobs. This parameter is configurable in `./run_with_slurm.sh` or `./run_with_slurm_podman.sh` scripts

## Contacts:
Oğuzhan Canpolat (aqwoguz [at] gmail [dot] com)  
