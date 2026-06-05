ReFrame tests
=============


Running weekly tests for production
-----------------------------------

**Note**: performance logs are only sent to syslog/ELK when run as user `vsc10001`.

```
# login to Hydra as vsc10001
~/reframe-tests/run_weekly.sh
```

Running tests in your account
-----------------------------

```
git clone https://github.com/vub-hpc/reframe-tests.git
reframe-tests/run.sh <options>
```

Examples
--------

```bash
# all Lmod tests as jobs in compute nodes
reframe-tests/run.sh -c lmod -r
# Lmod test LmodTestJavaMemory in the local node
reframe-tests/run.sh -c lmod -n LmodTestJavaMemory --system local -r
# OSU tests compiled with foss/2022a toolchain
reframe-tests/run.sh -c osu --valid_prog_environs foss-2022a -r
# OSU tests in ReFrame partition skylake-mn-mpi-ib
reframe-tests/run.sh -c osu --partitions skylake-mn-mpi-ib -r
# GROMACS GPU test in ReFrame partition zen2-ampere-sn-gpu
reframe-tests/run.sh -c gromacs_bench --partition zen2-ampere-sn-gpu -n GMXBenchMEMSingleNodeGPU -r
# Slurm tests as jobs in compute nodes
reframe-tests/run.sh -c slurm -r
# sofia-specific Slurm tests on manticore
# tests that should run in a job
reframe-tests/run.sh -c slurm_sofia --system manticore --tag job -r
# tests that should run locally
reframe-tests/run.sh -c slurm_sofia --system local --tag local -r
```

Location of ouput and log files
-------------------------------

All output is written to `VSC_SCRATCH_VO_USER/hpc-reframe-tests/`

* `logs/` ReFrame log files
* `perflogs/`: performance logs
* `stage/`: build and run scripts, (job) output, and (job) error files

Using old modules
-----------------

In VUB-HPC clusters, Lmod emits a warning message (and returns non-zero exit
code) when loading an old module, which breaks the ReFrame tests. To run
suppress the warning and non-zero exit code for old modules, run the tests as
follows:

```
REFRAME_QUIET_MODULE_LOAD=yes reframe-tests/run.sh <options>
```
