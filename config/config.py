import git
import os
from datetime import datetime

# log to syslog only with vsc10001 account
if os.getenv('USER') == 'vsc10001':
    syslog_level = 'info'
else:
    syslog_level = 'warning'

try:
    repo = git.Repo(os.path.dirname(os.path.dirname(__file__)))
    commit = f'{datetime.fromtimestamp(repo.head.commit.committed_date):%Y%m%d.%H%M}'
except Exception:
    commit = ''

perf_logging_format = 'reframe: ' + '|'.join([
    'username=%(osuser)s',
    'version=%(version)s',
    f'commit={commit}',
    'name=%(check_name)s',
    'system=%(check_system)s',
    'partition=%(check_partition)s',
    'environ=%(check_environ)s',
    'num_tasks=%(check_num_tasks)s',
    'num_cpus_per_task=%(check_num_cpus_per_task)s',
    'num_tasks_per_node=%(check_num_tasks_per_node)s',
    'modules=%(check_modules)s',
    'jobid=%(check_jobid)s',
    'perf_var=%(check_perf_var)s',
    'perf_value=%(check_perf_value)s',
    'unit=%(check_perf_unit)s',
])

environs_cpu = [
    'default',
    'foss-2022a',
    'intel-2022a',
    'foss-2023a',
    'intel-2023a',
    'foss-2024a',
    'intel-2024a',
]

environs_gpu = [
    'foss-2022a-cuda',
    'foss-2023a-cuda',
    'foss-2024a-cuda',
]

# workaround for old modules which emit a warning upon load and non-zero exit code
prepare_cmds = []
if os.getenv('REFRAME_QUIET_MODULE_LOAD', '').lower() in ['yes', '1', 'true']:
    prepare_cmds = [
        'shopt -s expand_aliases',
        "alias module='module -q'",
    ]

scheduler = 'slurm'

sched_options = {'use_nodes_option': True}

site_configuration = {
    'systems': [
        {
            'name': 'local',
            'descr': 'VUB-HPC local node',
            'hostnames': ['.*'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'local',
                    'scheduler': 'local',
                    'modules': [],
                    'access': [],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'tests in local node(s) (no job)',
                    'max_jobs': 1,
                    'launcher': 'local',
                },
                {
                    'name': 'local-mpi',
                    'scheduler': 'local',
                    'modules': [],
                    'access': [],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'MPI tests in local node(s) (no job)',
                    'max_jobs': 1,
                    'launcher': 'srun',
                },
            ],
        },
        {
            'name': 'hydra',
            'descr': 'VUB-HPC hydra cluster',
            'hostnames': ['.*'],
            'modules_system': 'lmod',
            'env_vars': [
                ['SLURM_CLUSTERS', 'hydra'],
                ['SLURM_CONF', '/etc/slurm/slurm.conf_hydra'],
                ['VSC_INSTITUTE_CLUSTER', 'hydra'],
            ],
            'partitions': [
                {
                    'name': 'skylake-sn',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=skylake,skylake_mpi'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'single-node jobs in Skylake nodes',
                    'max_jobs': 10,
                    'launcher': 'local',
                },
                {
                    'name': 'skylake-sn-mpi',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=skylake,skylake_mpi'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'single-node MPI jobs in Skylake nodes',
                    'max_jobs': 10,
                    'launcher': 'srun',
                },
                {
                    'name': 'skylake-mn-mpi-ib',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=skylake_mpi'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'multi-node MPI jobs in Skylake nodes with infiniband',
                    'max_jobs': 1,
                    'launcher': 'srun',
                },
                {
                    'name': 'skylake-mn-mpi-eth',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=skylake'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'multi-node MPI jobs in Skylake nodes without infiniband',
                    'max_jobs': 1,
                    'launcher': 'srun',
                },
                {
                    'name': 'broadwell-sn',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=broadwell'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'single-node jobs in Broadwell nodes',
                    'max_jobs': 10,
                    'launcher': 'local',
                },
                {
                    'name': 'broadwell-mpi',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=broadwell'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'MPI jobs in Broadwell nodes',
                    'max_jobs': 10,
                    'launcher': 'srun',
                },
                {
                    'name': 'zen4-sn',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=zen4'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'single-node jobs in Zen4 nodes',
                    'max_jobs': 10,
                    'launcher': 'local',
                },
                {
                    'name': 'zen4-mpi',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=zen4'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'MPI jobs in Zen4 nodes',
                    'max_jobs': 1,
                    'launcher': 'srun',
                },
                {
                    'name': 'zen5-sn',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=zen5_mpi'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'single-node jobs in Zen5 nodes',
                    'max_jobs': 10,
                    'launcher': 'local',
                },
                {
                    'name': 'zen5-mpi',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=zen5_mpi'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'MPI jobs in Zen5 nodes',
                    'max_jobs': 1,
                    'launcher': 'srun',
                },
                {
                    'name': 'broadwell-pascal-sn-gpu',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=pascal_gpu'],
                    'environs': environs_cpu + environs_gpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'single-node jobs in Broadwell nodes with Pascal P100 GPUs',
                    'max_jobs': 1,
                    'resources': [
                        {
                            'name': 'gpu',
                            'options': ['--gpus-per-node={num_gpus_per_node}'],
                        },
                    ],
                    'launcher': 'local',
                },
                {
                    'name': 'zen2-ampere-sn-gpu',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=ampere_gpu'],
                    'environs': environs_cpu + environs_gpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'single-node jobs in Zen2 nodes with Ampere A100 GPUs',
                    'max_jobs': 1,
                    'resources': [
                        {
                            'name': 'gpu',
                            'options': ['--gpus-per-node={num_gpus_per_node}'],
                        },
                    ],
                    'launcher': 'local',
                },
                {
                    'name': 'zen2-ampere-mpi',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=ampere_gpu'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'MPI jobs in Zen2 nodes',
                    'max_jobs': 1,
                    'launcher': 'srun',
                },
                {
                    'name': 'zen2-ampere-mpi-gpu',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=ampere_gpu'],
                    'environs': environs_cpu + environs_gpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'MPI jobs in Zen2 nodes with Ampere A100 GPUs',
                    'max_jobs': 1,
                    'resources': [
                        {
                            'name': 'gpu',
                            'options': ['--gpus-per-node={num_gpus_per_node}'],
                        },
                    ],
                    'launcher': 'srun',
                },
            ],
        },
        {
            'name': 'anansi',
            'descr': 'VUB-HPC anansi cluster',
            'hostnames': ['.*'],
            'modules_system': 'lmod',
            'env_vars': [
                ['SLURM_CLUSTERS', 'anansi'],
                ['SLURM_CONF', '/etc/slurm/slurm.conf_anansi'],
                ['VSC_INSTITUTE_CLUSTER', 'anansi'],
            ],
            'partitions': [
                {
                    'name': 'broadwell-sn',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=pascal_gpu'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'single-node jobs in Broadwell nodes',
                    'max_jobs': 1,
                    'launcher': 'local',
                },
                {
                    'name': 'broadwell-pascal-sn-gpu',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=pascal_gpu'],
                    'environs': environs_cpu + environs_gpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'single-node jobs in Broadwell nodes with GTX 1080 Ti GPUs',
                    'max_jobs': 1,
                    'resources': [
                        {
                            'name': 'gpu',
                            'options': ['--gpus-per-node={num_gpus_per_node}'],
                        },
                    ],
                    'launcher': 'local',
                },
            ],
        },
        {
            'name': 'manticore',
            'descr': 'VUB-HPC manticore cluster',
            'hostnames': ['.*'],
            'modules_system': 'lmod',
            # 'modules': ['cluster/manticore'],  # does not work for some reason, set envars explicitly instead
            'env_vars': [
                ['SLURM_CLUSTERS', 'manticore'],
                ['SLURM_CONF', '/etc/slurm/slurm.conf_manticore'],
                ['VSC_INSTITUTE_CLUSTER', 'manticore'],
            ],
            'partitions': [
                {
                    'name': 'zen3-sn',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=zen3'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'single-node jobs in (virtualized) Zen3 nodes',
                    'max_jobs': 10,
                    'launcher': 'local',
                },
                {
                    'name': 'zen3-mpi',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=zen3_mpi'],
                    'environs': environs_cpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'MPI jobs in (virtualized) Zen3 nodes',
                    'max_jobs': 1,
                    'launcher': 'srun',
                },
                {
                    'name': 'zen3-ampere-sn-gpu',
                    'scheduler': scheduler,
                    'sched_options': sched_options,
                    'modules': [],
                    'access': ['--partition=ampere_gpu'],
                    'environs': environs_cpu + environs_gpu,
                    'prepare_cmds': prepare_cmds,
                    'descr': 'single-node jobs in (virtualized) Zen3 nodes with (fake!) Ampere A100 GPUs',
                    'max_jobs': 1,
                    'resources': [
                        {
                            'name': 'gpu',
                            'options': ['--gpus-per-node={num_gpus_per_node}'],
                        },
                    ],
                    'launcher': 'local',
                },
            ],
        },
    ],
    'environments': [
        {'name': 'default', 'cc': 'gcc', 'cxx': 'g++', 'ftn': 'gfortran'},
        {
            'name': 'foss-2022a',
            'modules': ['foss/2022a', 'Autotools/20220317-GCCcore-11.3.0'],
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
        },
        {
            'name': 'intel-2022a',
            'modules': ['intel/2022a', 'Autotools/20220317-GCCcore-11.3.0'],
            'cc': 'mpiicc',
            'cxx': 'mpiicpc',
            'ftn': 'mpiifort',
        },
        {
            'name': 'foss-2023a',
            'modules': ['foss/2023a', 'Autotools/20220317-GCCcore-12.3.0'],
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
        },
        {
            'name': 'intel-2023a',
            'modules': ['intel/2023a', 'Autotools/20220317-GCCcore-12.3.0'],
            'cc': 'mpiicc',
            'cxx': 'mpiicpc',
            'ftn': 'mpiifort',
        },
        {
            'name': 'foss-2024a',
            'modules': ['foss/2024a', 'Autotools/20231222-GCCcore-13.3.0'],
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
        },
        {
            'name': 'intel-2024a',
            'modules': ['intel/2024a', 'Autotools/20231222-GCCcore-13.3.0'],
            'cc': 'mpiicx',
            'cxx': 'mpiicpx',
            'ftn': 'mpiifx',
        },
        {
            'name': 'foss-2022a-cuda',
            'modules': ['foss/2022a', 'CUDA/11.7.0', 'Autotools/20220317-GCCcore-11.3.0'],
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
        },
        {
            'name': 'foss-2023a-cuda',
            'modules': ['foss/2023a', 'CUDA/12.1.1', 'Autotools/20220317-GCCcore-12.3.0'],
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
        },
        {
            'name': 'foss-2024a-cuda',
            'modules': ['foss/2024a', 'CUDA/12.6.0', 'Autotools/20231222-GCCcore-13.3.0'],
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
        },
    ],
    'logging': [
        {
            'perflog_compat': True,
            'level': 'debug',
            'handlers': [
                {
                    'type': 'file',
                    'name': os.path.join(os.getenv('RFM_OUTPUT_DIR', os.curdir), 'logs', 'reframe.log'),
                    'level': 'debug',
                    'format': '[%(asctime)s] %(levelname)s: %(check_name)s: %(message)s',  # noqa: E501
                    'append': False,
                    'timestamp': "%Y%m%d_%H%M%S",
                },
                {
                    'type': 'stream',
                    'name': 'stdout',
                    'level': 'info',
                    'format': '%(message)s',
                },
                {
                    'type': 'file',
                    'name': os.path.join(os.getenv('RFM_OUTPUT_DIR', os.curdir), 'logs', 'reframe.out'),
                    'level': 'info',
                    'format': '%(message)s',
                    'append': False,
                    'timestamp': "%Y%m%d_%H%M%S",
                },
            ],
            'handlers_perflog': [
                {
                    'type': 'filelog',
                    'prefix': '%(check_system)s/%(check_partition)s',
                    'level': 'info',
                    'format': '%(check_job_completion_time)s ' + perf_logging_format,
                    'append': True,
                },
                {
                    'type': 'syslog',
                    'address': '/dev/log',
                    'level': syslog_level,
                    'format': perf_logging_format,
                    'append': True,
                },
            ],
        }
    ],
    'general': [
        {
            'check_search_path': ['checks/'],
            'check_search_recursive': True,
            'purge_environment': True,
            'resolve_module_conflicts': False,  # prevent that ReFrame loads modules before submitting the job
            'keep_stage_files': True,
        }
    ],
}
