import os
import reframe as rfm
import reframe.core.runtime as rt
import reframe.utility.sanity as sn

# 'gpu' lists are tuples of (partition, default_cpus_per_gpu)
PARTITION_MAP = {
    'sofia': {
        'gpu': [('zen4_h200', 24)],
        'mpi': ['zen5_dense', 'zen5_himem'],
    },
    'manticore': {
        'gpu': [('ampere_gpu', 2)],
        'smp': ['zen3'],
        'mpi': ['zen3_mpi'],
    },
}

# example: "tres_alloc_str": "cpu=4,mem=14576M,node=2,billing=4,gres\/gpu:a100=2"
GET_GPUS_CPUS = r"""
scontrol show job $SLURM_JOB_ID --json | jq -r '
  .jobs[0] |
  .tres_alloc_str as $tres |
  "cpus = \($tres | capture("cpu=(?<c>[0-9]+)") // {c:"0"} | .c)\n" +
  "gpus = \($tres | capture("gres/gpu:[^=]*=(?<g>[0-9]+)") // {g:"0"} | .g)"
'
"""

TEMPJOB = r"""
jobid=$(sbatch --parsable --time=5:0 --job-name={job_name} --wrap=hostname \
    --cluster={cluster} --partition={slurm_partition} {extra})
exitcode=$?
if [[ $exitcode -ne 0 ]]; then exit $exitcode; fi
jobid=${{jobid%%;*}}
if [[ -n $jobid ]]; then
    echo job submitted: $jobid
    scancel $jobid
fi
"""


class SlurmSofiaBase(rfm.RunOnlyRegressionTest):
    """ Base class for Slurm tests on Sofia """
    descr = "Slurm test"
    valid_systems = required
    valid_prog_environs = required
    time_limit = '10m'
    cluster = variable(str, value=os.getenv('VSC_DEFAULT_CLUSTER_MODULE', 'undefined'))

    @run_after('setup')
    def get_cluster_info(self):
        system = rt.runtime().system.name
        if system != 'local':
            self.cluster = system

        if self.cluster in PARTITION_MAP:
            self.default_cpus_per_gpu = PARTITION_MAP[self.cluster]['gpu'][0][1]
            self.gpu_partition = PARTITION_MAP[self.cluster]['gpu'][0][0]
            self.cpu_partition = PARTITION_MAP[self.cluster]['mpi'][0][0]
        else:
            raise KeyError(f'Cluster {self.cluster} is not supported by this test')


@rfm.simple_test
class SbatchDefaultCPUPerGPU(SlurmSofiaBase):
    descr += ": sbatch allocates default #CPU cores per GPU"
    gpus = 1
    executable = GET_GPUS_CPUS
    tags.add('job')
    num_tasks = None  # avoid that ReFrame sets --ntasks in Slurm job
    num_nodes = None  # avoid that ReFrame sets --nodes in Slurm job

    @run_before('run')
    def add_slurm_options(self):
        self.job.options = [
            f'--gpus-per-node={self.gpus}',
        ]

    @sanity_function
    def assert_allocation(self):
        cpus = self.gpus * self.default_cpus_per_gpu
        return sn.all([
            sn.assert_found(rf'^cpus = {cpus}$', self.stdout, self.descr),
            sn.assert_found(rf'^gpus = {self.gpus}$', self.stdout, self.descr),
            sn.assert_not_found(".", self.stderr, 'there should be no error messages'),
        ])


class SlurmSofiaBaseLocal(SlurmSofiaBase):
    """
    Base class for tests with Slurm jobs submitted locally
    """
    tags.add('local')
    extra_job_opts = "--hold"


@rfm.simple_test
class SbatchNoGPUs(SlurmSofiaBaseLocal):
    descr += ": not requesting any GPUs in the GPU partition"

    @run_after('setup')
    def set_executable(self):
        self.executable = TEMPJOB.format(
            cluster=self.cluster,
            slurm_partition=self.gpu_partition,
            job_name=self.__class__.__name__,
            extra=self.extra_job_opts)

    @sanity_function
    def assert_allocation(self):
        error_msg = 'Only GPU jobs are allowed on this partition'
        return sn.all([
            sn.assert_found(error_msg, self.stderr, f'error message should contain: "{error_msg}"'),
            sn.assert_eq(self.job.exitcode, 1, f'exit code should be 1, got {self.job.exitcode}'),
        ])


@rfm.simple_test
class SbatchForbiddenCPUOptions(SlurmSofiaBaseLocal):
    descr += ": requesting forbidden CPU options in the GPU partition"
    job_opts = parameter([
        '--ntasks-per-core=1',
        '--threads-per-core=1',
        '--ntasks-per-socket=1',
    ])

    @run_after('setup')
    def set_executable(self):
        self.executable = TEMPJOB.format(
            cluster=self.cluster,
            slurm_partition=self.gpu_partition,
            job_name=self.__class__.__name__,
            extra=f"{self.extra_job_opts} --gpus-per-node=3 {self.job_opts}")

    @sanity_function
    def assert_allocation(self):
        error_msg = f'Job option {self.job_opts.split("=")[0]} is not allowed on this partition'
        return sn.all([
            sn.assert_found(error_msg, self.stderr, f'error message should contain: "{error_msg}"'),
            sn.assert_eq(self.job.exitcode, 1, f'exit code should be 1, got {self.job.exitcode}'),
        ])


@rfm.simple_test
class SbatchCorrectCPUsPerGPU(SlurmSofiaBaseLocal):
    descr += ": requesting correct #CPU cores per GPU"
    job_opts = parameter([
        ['--cpus-per-gpu={cpus} --gpus-per-node={gpus}', 2, lambda x, y: x],
        ['--ntasks-per-gpu={cpus} --gpus-per-node={gpus}', 2, lambda x, y: x],
        ['--ntasks-per-node={cpus} --gpus-per-node={gpus}', 2, lambda x, y: x * y],
        ['--ntasks-per-node={cpus} --nodes=2 --gpus-per-node={gpus}', 2, lambda x, y: x * y],
        ['--ntasks-per-node={cpus} --gpus=4 --gpus-per-node={gpus}', 2, lambda x, y: x * y],
        ['--ntasks={cpus} --nodes=1 --gpus-per-node={gpus}', 2, lambda x, y: x * y],
    ], fmt=lambda x: x[0])

    @run_after('setup')
    def set_executable(self):
        job_opts, gpus, modifier = self.job_opts
        job_opts = job_opts.format(cpus=modifier(self.default_cpus_per_gpu, gpus), gpus=gpus)
        self.executable = TEMPJOB.format(
            cluster=self.cluster,
            slurm_partition=self.gpu_partition,
            job_name=self.__class__.__name__,
            extra=f"{self.extra_job_opts} {job_opts}")

    @sanity_function
    def assert_allocation(self):
        msg = r'job submitted: \d+$'
        return sn.all([
            sn.assert_found(msg, self.stdout, f'standard output should contain: "{msg}"'),
            sn.assert_eq(self.job.exitcode, 0, f'exit code should be 0, got {self.job.exitcode}'),
        ])


@rfm.simple_test
class SbatchWrongCPUsPerGPU(SbatchCorrectCPUsPerGPU):
    descr += ": requesting wrong #CPU cores per GPU"
    job_opts = parameter([
        ['--cpus-per-gpu={cpus} --gpus-per-node={gpus}', 2, lambda x, y: x - 1],
        ['--ntasks-per-gpu={cpus} --gpus-per-node={gpus}', 2, lambda x, y: x - 1],
        ['--ntasks-per-node={cpus} --gpus-per-node={gpus}', 2, lambda x, y: x * y - 1],
        ['--ntasks-per-node={cpus} --nodes=2 --gpus-per-node={gpus}', 2, lambda x, y: x * y - 1],
        ['--ntasks-per-node={cpus} --gpus=4 --gpus-per-node={gpus}', 2, lambda x, y: x * y - 1],
        ['--ntasks={cpus} --nodes=1 --gpus-per-node={gpus}', 2, lambda x, y: x * y - 1],
    ], fmt=lambda x: x[0])

    @sanity_function
    def assert_allocation(self):
        error_msg = f'This partition requires exactly {self.default_cpus_per_gpu} CPUs per GPU'
        return sn.all([
            sn.assert_found(error_msg, self.stderr, f'error message should contain: "{error_msg}"'),
            sn.assert_eq(self.job.exitcode, 1, f'exit code should be 1, got {self.job.exitcode}'),
        ])


@rfm.simple_test
class SbatchForbiddenCombination(SlurmSofiaBaseLocal):
    descr += ": requesting forbidden combination of CPU options"
    gpus = 2
    job_opts = parameter([
        f'--cpus-per-task=2 --gpus-per-node={gpus}',
        f'--cpus-per-task=2 --nodes=2 --gpus-per-node={gpus}',
        f'--ntasks=2 --nodes=2 --gpus-per-node={gpus}',
        f'--ntasks=3 --ntasks-per-node=2 --gpus-per-node={gpus}',
        f'--gpus-per-task=1 --ntasks=2 --cpus-per-task=2 --gpus-per-node={gpus}',
        f'--gpus={gpus}',
    ])

    @run_after('setup')
    def set_executable(self):
        self.executable = TEMPJOB.format(
            cluster=self.cluster,
            slurm_partition=self.gpu_partition,
            job_name=self.__class__.__name__,
            extra=f"{self.extra_job_opts} {self.job_opts}")

    @sanity_function
    def assert_allocation(self):
        error_msg = 'The requested resource combination is not allowed on this partition'
        return sn.all([
            sn.assert_found(error_msg, self.stderr, f'error message should contain: "{error_msg}"'),
            sn.assert_eq(self.job.exitcode, 1, f'exit code should be 1, got {self.job.exitcode}'),
        ])


@rfm.simple_test
class SbatchForbiddenMemOptions(SlurmSofiaBaseLocal):
    descr += ": requesting forbidden memory options"
    job_opts = parameter([
        '--mem=1000',
        '--mem-per-cpu=1000',
        '--mem-per-gpu=1000 --gpus-per-node=1',
    ])

    @run_after('setup')
    def set_executable(self):
        if self.job_opts.startswith('--mem-per-gpu'):
            slurm_partition = self.gpu_partition
        else:
            slurm_partition = self.cpu_partition

        self.executable = TEMPJOB.format(
            cluster=self.cluster,
            slurm_partition=slurm_partition,
            job_name=self.__class__.__name__,
            extra=f"{self.extra_job_opts} {self.job_opts}")

    @sanity_function
    def assert_allocation(self):
        error_msg = (f'Job submit option {self.job_opts.split("=")[0]} is not allowed: memory is assigned '
                     'automatically per CPU core')
        return sn.all([
            sn.assert_found(error_msg, self.stderr, f'error message should contain: "{error_msg}"'),
            sn.assert_eq(self.job.exitcode, 1, f'exit code should be 1, got {self.job.exitcode}'),
        ])
