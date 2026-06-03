import os
import reframe as rfm
import reframe.utility.sanity as sn

src_name = 'cp2k'
src_version = '6.1'  # this is the version of the test, not necessarily the version of the software!
src_dir = f'{src_name}-{src_version}'
src_path = os.path.join(os.environ['REFRAME_SOURCEPATH'], src_name[0].lower(), src_name.upper(), f'{src_dir}.tar.bz2')
testfile = 'H2O-128'
dir_cmd = (
    f'mkdir {src_dir} && cd {src_dir}'
    f' && tar -xvf {src_path} {src_name}-{src_version}/tests/QS/benchmark/{testfile}.inp --strip-components 4'
)


class CP2KTestBase(rfm.RunOnlyRegressionTest):
    "base class for CP2K tests"
    descr = f'CP2K test {testfile}'
    valid_systems = required
    valid_prog_environs = ['default']
    executable = 'cp2k.popt'
    executable_opts = ['-i', f'{testfile}.inp']
    time_limit = '20m'
    env_vars = {
        'OMP_NUM_THREADS': '1',  # necessary when running with MPI
    }
    exclusive_access = required
    modules = required
    num_tasks = required
    num_cpus_per_task = 1
    prerun_cmds = [dir_cmd]

    @sanity_function
    def assert_energy(self):
        energy = sn.extractsingle(
            r'\s+ENERGY\| Total FORCE_EVAL \( QS \) energy \[.+\].+ (?P<energy>\S+)$',
            self.stdout, 'energy', float, item=-1)
        energy_ref = -2202.1791
        energy_diff = sn.abs(energy - energy_ref)
        step_count_ref = 10
        return sn.all([
            sn.assert_found(r'PROGRAM STOPPED IN', self.stdout),
            sn.assert_eq(sn.count(sn.extractall(
                r'(?P<step_count>Step number)',
                self.stdout, 'step_count')), step_count_ref),
            sn.assert_lt(energy_diff, 1e-4)
        ])

    @performance_function('s', perf_key='time')
    def time(self):
        return sn.extractsingle(r'^ CP2K(\s+[\d\.]+){4}\s+(?P<perf>\S+)', self.stdout, 'perf', float)


@rfm.simple_test
class CP2KTestSingleNode(CP2KTestBase):
    descr += ' single-node, multi-core'

    @run_after('init')
    def post_init(self):
        self.num_tasks_per_node = self.num_tasks


@rfm.simple_test
class CP2KTestMultiNode(CP2KTestBase):
    descr += ' multi-node'
    num_tasks_per_node = required
