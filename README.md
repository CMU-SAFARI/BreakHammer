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

1. Clone the repository `git clone git@github.com:kirbyydoge/breakhammer.git`
3. Install python dependencies, build Ramulator2, and download traces with `./run_simple_test.sh`

## Example Use

1. Run Ramulator2 simulations `./run_with_slurm.sh` (If you do not have slurm use `./run_with_personalcomputer.sh` instead)
2. Wait for the simulations to finish. You can use `./check_run_status.sh` to track run status (this script also creates intermediate scripts that can restart failed runs)
3. Parse simulation results and collects statistics with `./parse_results.sh`
4. Generate figures with `./plot_all.sh`

## Contacts:
Oğuzhan Canpolat (aqwoguz [at] gmail [dot] com)  
