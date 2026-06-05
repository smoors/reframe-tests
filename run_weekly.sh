#!/bin/bash

cd $(dirname "$0")

cmds=(
    # shared storage test
    "./run.sh -c ior --partitions skylake-mn-mpi-ib -r"
    "./run.sh -c ior --partitions skylake-mn-mpi-eth -r"
    "./run.sh -c ior --partitions zen5-mpi -r"

    # multi-node tests
    "./run.sh -c osu"
    "./run.sh -c gromacs_bench -n GMXBenchMEMMultiNode -r"
    "./run.sh -c cp2k_tests -n CP2KTestMultiNode -r"

    # single-node tests
    "./run.sh -c blas-tester -r"
    "./run.sh -c gromacs_bench -n GMXBenchMEMSingleNode -r"
    "./run.sh -c gromacs_bench -n GMXBenchMEMSingleNodeGPU -r"
    "./run.sh -c cp2k_tests -n CP2KTestSingleNode -r"
)

total=0
for cmd in "${cmds[@]}"; do
    echo "$cmd"
    eval "$cmd"
    exitcode=$?
    ((total+=exitcode))
done

exit ${total:-0}
