#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter
import os
from pprint import pprint
import sys


class CustomFormatter(ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter):
    pass


parser = ArgumentParser(
    formatter_class=CustomFormatter,
    epilog='''
* options '--checkpath' and '--name' correspond to the ReFrame options with the same name
* options '--system' and '--partitions' set ReFrame options '--system' and '--setvar valid_systems='
* option '--valid_prog_environs' sets ReFrame option '--setvar valid_prog_environs='

any additional options not listed here are passed directly to ReFrame
''',
)

parser.add_argument('-c', '--checkpath', dest='checkpath', required=True,
                    help='path (relative to this script) of test directory or script')
parser.add_argument('-n', '--name', dest='name', action='append',
                    help='check name')
parser.add_argument('--system', dest='system', choices=['anansi', 'hydra', 'local', 'manticore', 'sofia'],
                    default='hydra', help='run tests in given cluster')
parser.add_argument('--partitions', dest='partitions',
                    help='comma-separated list of ReFrame partitions')
parser.add_argument('--valid_prog_environs', dest='valid_prog_environs',
                    help='comma-separated list of programming environments')

args, extra_args = parser.parse_known_args()

system = args.system
checkpath = args.checkpath
name = args.name

tests = [
    {
        'checkpath': 'blas-tester',
        'valid_prog_environs': ['foss-2024a', 'intel-2024a'],
        'valid_systems': {
            'hydra': ['hydra:zen4-sn', 'hydra:zen5-sn'],
            'manticore': ['manticore:zen3-sn'],
            'local': ['local:local'],
        },
        'setvar_extra': {
            'num_cpus_per_task': '4',
            'BLASTest.exclusive_access': 'false',
        },
        'extra': {
            'exec-policy': 'serial',
        },
    },
    {
        'checkpath': 'cp2k_tests',
        'name': ['CP2KTestSingleNode'],
        'valid_systems': {
            'hydra': ['hydra:zen4-mpi', 'hydra:zen5-mpi'],
            'manticore': ['manticore:zen3-mpi'],
            'local': ['local:local'],
        },
        'setvar_extra': {
            'modules': 'CP2K/2025.2-foss-2025a',
            'num_tasks': '4',
            'num_tasks_per_node': '4',
            'exclusive_access': 'false',
        },
        'extra': {
            'exec-policy': 'serial',
        },
    },
    {
        'checkpath': 'cp2k_tests',
        'name': ['CP2KTestMultiNode'],
        'valid_systems': {
            'hydra': ['hydra:zen4-mpi', 'hydra:zen5-mpi'],
            'local': ['local:local-mpi'],
        },
        'setvar_extra': {
            'modules': 'CP2K/2025.2-foss-2025a',
            'num_tasks': '4',
            'num_tasks_per_node': '1',
            'exclusive_access': 'false',
        },
        'extra': {
            'exec-policy': 'serial',
        },
    },
    {
        'checkpath': 'gromacs_bench',
        'name': ['GMXBenchMEMMultiNode'],
        'valid_systems': {
            'hydra': ['hydra:zen4-mpi', 'hydra:zen5-mpi'],
            'local': ['local:local-mpi'],
        },
        'setvar_extra': {
            'modules': 'GROMACS/2023.3-foss-2023a',
            'num_tasks': '4',
            'num_tasks_per_node': '1',
            'exclusive_access': 'false',
        },
        'extra': {
            'exec-policy': 'serial',
        },
    },
    {
        'checkpath': 'gromacs_bench',
        'name': ['GMXBenchMEMSingleNode'],
        'valid_systems': {
            'hydra': ['hydra:zen4-sn', 'hydra:zen5-sn'],
            'manticore': ['manticore:zen3-sn'],
            'local': ['local:local'],
        },
        'setvar_extra': {
            'modules': 'GROMACS/2023.3-foss-2023a',
            'num_cpus_per_task': '4',
            'exclusive_access': 'false',
        },
        'extra': {
            'exec-policy': 'serial',
        },
    },
    {
        'checkpath': 'gromacs_bench',
        'name': ['GMXBenchMEMSingleNodeGPU'],
        'valid_systems': {
            'hydra': ['hydra:zen2-ampere-sn-gpu'],
            'local': ['local:local'],
        },
        'setvar_extra': {
            'modules': 'GROMACS/2023.3-foss-2023a-CUDA-12.1.1-PLUMED-2.9.0',
            'num_cpus_per_task': '4',
            'num_gpus_per_node': '1',
            'exclusive_access': 'false',
        },
        'extra': {
            'exec-policy': 'serial',
        },
    },
    {
        'checkpath': 'ior',
        'valid_prog_environs': ['foss-2024a'],
        'valid_systems': {
            'hydra': ['hydra:zen5-mpi'],
            'local': ['local:local-mpi'],
        },
        'setvar_extra': {
            'iorBuildTest.num_cpus_per_task': '4',
            'iorWriteTest.num_tasks': '4',
            'iorReadTest.num_tasks': '4',
            'iorWriteTest.exclusive_access': 'false',
            'iorReadTest.exclusive_access': 'false',
        },
        'extra': {
            'exec-policy': 'serial',
            'job-option': 'mem-per-cpu=4G',
        },
    },
    {
        'checkpath': 'lmod',
        'valid_systems': {
            'hydra': ['hydra:zen4-sn'],
            'manticore': ['manticore:zen3-sn'],
            'local': ['local:local'],
        },
        'extra': {
            'job-option': 'mem-per-cpu=1G',
        },
    },
    {
        'checkpath': 'osu',
        'valid_prog_environs': ['foss-2024a', 'intel-2024a'],
        'valid_systems': {
            'hydra': ['hydra:zen4-mpi', 'hydra:zen5-mpi'],
            'manticore': ['manticore:zen3-mpi'],
            'local': ['local:local-mpi'],
        },
        'setvar_extra': {
            'OSULatencyTest.num_tasks': '2',
            'OSUBandwidthTest.num_tasks': '2',
            'OSUBuildTest.num_cpus_per_task': '4',
            'OSULatencyTest.exclusive_access': 'false',
            'OSUBandwidthTest.exclusive_access': 'false',
        },
        'extra': {
            'exec-policy': 'serial',
            'tag': 'prod_small',
        },
    },
    {
        'checkpath': 'slurm',
        'valid_systems': {
            'hydra': ['hydra:zen4-sn'],
            'manticore': ['manticore:zen3-sn'],
            'anansi': ['anansi:zen5-ada-sn-gpu'],
            'local': ['local:local'],
        },
    },
    {
        'checkpath': 'slurm_gpu',
        'name': ['GPUBinding'],
        'valid_systems': {
            'hydra': ['hydra:zen2-ampere-sn-gpu'],
            'local': ['local:local'],
        },
        'extra': {
            'job-option': 'mem-per-cpu=1G',
        },
    },
    {
        'checkpath': 'slurm_sofia',
        'valid_systems': {
            'sofia': ['sofia:zen4-h200-mpi-gpu'],
            'manticore': ['manticore:zen3-ampere-sn-gpu'],
            'local': ['local:local'],
        },
    },
]

selected_tests = []
for test in tests:
    if checkpath == test['checkpath'] or checkpath.startswith(test['checkpath'] + os.sep):
        if not name or not test.get('name') or name == test.get('name'):
            selected_tests.append(test)

num_selected = len(selected_tests)
if num_selected != 1:
    print(f'ERROR: {num_selected} tests selected, exactly 1 is required. Add option --name to narrow selection.')
    pprint(selected_tests)
    sys.exit(1)

selected = selected_tests[0]

if args.partitions:
    partitions = args.partitions.split(',')
    valid_systems = [f'{system}:{x}' for x in partitions]
else:
    valid_systems = selected['valid_systems'][system]

if args.valid_prog_environs:
    valid_prog_environs = args.valid_prog_environs.split(',')
else:
    valid_prog_environs = selected.get('valid_prog_environs', ['default'])

name = selected.get('name', []) if not name else name

cmd = [
    'reframe --run --performance-report',
    f'--checkpath {checkpath}',
    ' '.join([f'--name {x}' for x in name]),
    f'--system {system}',
    f'--setvar valid_prog_environs={",".join(valid_prog_environs)}',
    f'--setvar valid_systems={",".join(valid_systems)}',
]

if selected.get('setvar_extra'):
    for key, val in selected['setvar_extra'].items():
        cmd.append(f'--setvar {key}={val}')

if selected.get('extra'):
    for key, val in selected['extra'].items():
        cmd.append(f'--{key} {val}')

cmd.extend(extra_args)

print(' '.join(cmd))
os.system(' '.join(cmd))
