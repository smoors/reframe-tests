import json
import filecmp
import os
import reframe as rfm
import reframe.utility.sanity as sn
from datetime import date, datetime


# check if memory in JAVA_TOOL_OPTIONS is set correctly
# uses cgroups v2
# only works in a job
check_java_memory = """
import os, re
cgroup = open('/proc/self/cpuset', encoding='utf-8').read().rstrip()
mem_file = f'/sys/fs/cgroup/{cgroup}/../../../memory.max'
mem_alloc = open(mem_file, encoding='utf-8').read().rstrip()
mem_java = os.environ['JAVA_TOOL_OPTIONS'].replace('-Xmx', '')
print(int(int(mem_alloc) * 0.8), int(mem_java))
print(int(int(mem_alloc) * 0.8) == int(mem_java))
"""

OLDEST_TCGEN = 2022


def calc_tcgen(months):
    "calculate the toolchain generation for a date corresponding to now - months"
    curtimestamp = datetime.now().timestamp()
    newtimestamp = curtimestamp - months * 2629743  # 1 month = 2629743 seconds, as defined in SitePackage.lua
    newdate = date.fromtimestamp(newtimestamp)
    return f'{newdate.year}a'


class LmodTestBase(rfm.RunOnlyRegressionTest):
    descr = "test Lmod"
    valid_systems = required
    valid_prog_environs = required
    time_limit = '10m'
    num_tasks = 1
    num_tasks_per_node = 1
    num_cpus_per_task = 1


@rfm.simple_test
class LmodTestConfig(LmodTestBase):
    descr += ": configuration"
    executable = ' && '.join([
        'module --config-json 2>config.json',
        'echo $VSC_INSTITUTE_CLUSTER-$VSC_ARCH_LOCAL$VSC_ARCH_SUFFIX',
    ])

    @sanity_function
    def assert_config(self):
        config = json.load(open('config.json', 'r'))['configT']
        configroot = '/etc/lmod'
        return sn.all([
            sn.assert_found(config['sysName'], self.stdout, 'System name'),
            sn.assert_eq(config['siteName'], 'VUB_HPC', 'Site name'),
            sn.assert_eq(config['spdr_ignore'], 'no', 'Ignore Cache'),
            sn.assert_eq(config['disp_av_ext'], 'yes', 'Display Extension w/ avail'),
            sn.assert_eq(config['autoSwap'], 'no', 'Auto swapping'),
            sn.assert_eq(config['colorize'], 'yes', 'Colorize Lmod'),
            sn.assert_eq(config['disable1N'], 'yes', 'Disable Same Name AutoSwap'),
            sn.assert_eq(config['dupPaths'], 'no', 'Allow duplicate paths'),
            sn.assert_eq(config['exactMatch'], 'no', 'Require Exact Match/no defaults'),
            sn.assert_eq(config['expMCmd'], 'yes', 'Export the module command'),
            sn.assert_eq(config['extendDflt'], 'no', 'Allow extended default'),
            sn.assert_eq(config['lang'], 'en', 'Language used for err/msg/warn'),
            sn.assert_eq(config['lang_site'], f'{configroot}/lang.lua', 'Site message file'),
            sn.assert_eq(config['ld_lib_path'], '<empty>', 'LD_LIBRARY_PATH at config time'),
            sn.assert_eq(config['ld_preload'], '<empty>', 'LD_PRELOAD at config time'),
            sn.assert_eq(config['pin_v'], 'yes', 'Pin Versions in restore'),
            sn.assert_eq(config['redirect'], 'yes', 'Redirect to stdout'),
            sn.assert_eq(config['sitePkg'], f'{configroot}/SitePackage.lua', 'Site Pkg location'),
            sn.assert_eq(config['tm_ancient'], 86400, 'User cache valid time(sec)'),
            sn.assert_eq(config['tm_short'], 86400, 'Write cache after (sec)'),
            sn.assert_eq(config['z01_admin'], f'{configroot}/admin.list', 'Admin file'),
            sn.assert_eq(config['spdr_loads'], 'yes', 'Cached loads'),
        ])


@rfm.simple_test
class LmodTestModulepath(LmodTestBase):
    descr += ": check the MODULEPATH environment variable"
    executable = ''

    @sanity_function
    def assert_modulepath(self):
        modulepaths = os.environ['MODULEPATH'].split(':')
        # remove empty paths
        modulepaths = [x for x in modulepaths if x]
        return sn.all([
            sn.assert_true('/apps/brussel' in x or '/etc/modulefiles', x) for x in modulepaths
        ])


@rfm.simple_test
class LmodTestAvail(LmodTestBase):
    descr += ": show available modules"
    executable = 'time -p module av'

    @sanity_function
    def assert_output(self):
        realtime = sn.extractsingle(r'^real (\S+)$', self.stderr, 1, float)
        return sn.all([
            sn.assert_found(rf' foss/{calc_tcgen(12)}', self.stdout, f'foss/{calc_tcgen(12)}'),
            sn.assert_found(r' Python/', self.stdout, 'Python'),
            sn.assert_found(r' R/', self.stdout, 'R'),
            sn.assert_found(
                r'^If you need software that is not listed, request it at hpc@vub.be$',
                self.stdout,
                'message: If you need software that is not listed'
            ),
            sn.assert_lt(realtime, 5, 'command runs in less then 5 seconds'),
        ])


@rfm.simple_test
class LmodTestSpider(LmodTestBase):
    descr += ": show available versions of a module"
    executable = 'module --terse spider foss/'

    @sanity_function
    def assert_output(self):
        return sn.all([
            sn.assert_found(rf'^foss/{calc_tcgen(12)}$', self.stdout, f'foss/{calc_tcgen(12)}'),
            sn.assert_found(rf'^foss/{calc_tcgen(24)}$', self.stdout, f'foss/{calc_tcgen(24)}'),
        ])


class LmodTestLoad(LmodTestBase):
    descr += ": load a module"
    toolchain = f'foss/{calc_tcgen(24)}'
    check_commands = [
        'command -v gcc',
        'command -v mpirun',
        'command -v ld',
    ]
    postrun_cmds = ['echo $LD_LIBRARY_PATH | tr ":" "\n" >ld_lib_path']

    @run_after('init')
    def set_executable(self):
        exe = [f'{self.moduleload} {self.toolchain}', self.modulelist] + self.check_commands
        self.executable = ';'.join(exe)

    @sanity_function
    def assert_output(self):
        return sn.all([
            sn.assert_found(rf'^{self.toolchain}$', self.stdout, self.toolchain),
            sn.assert_found(r'^/apps/brussel/\S+/gcc$', self.stdout, 'gcc'),
            sn.assert_found(r'^/apps/brussel/\S+/mpirun$', self.stdout, 'mpirun'),
            sn.assert_found(r'^/apps/brussel/\S+/ld$', self.stdout, 'ld'),
            sn.assert_found(r'^/apps/brussel/\S+/FFTW/\S+/lib$', 'ld_lib_path', 'FFTW'),
            sn.assert_found(r'^/apps/brussel/\S+/zlib/\S+/lib$', 'ld_lib_path', 'zlib'),
            sn.assert_found(r'^/apps/brussel/\S+/XZ/\S+/lib$', 'ld_lib_path', 'XZ'),
            sn.assert_found(r'^/apps/brussel/\S+/binutils/\S+/lib$', 'ld_lib_path', 'binutils'),
        ])


@rfm.simple_test
class LmodTestLoadmodule(LmodTestLoad):
    moduleload = 'module load'
    modulelist = 'module --terse list'


@rfm.simple_test
class LmodTestLoadml(LmodTestLoad):
    moduleload = 'ml'
    modulelist = 'ml --terse'


@rfm.simple_test
class LmodTestPurge(LmodTestBase):
    descr += ": purge all modules"
    toolchain = f'foss/{calc_tcgen(12)}'
    executable = f'module load {toolchain}; module purge; module list'
    # need to purge first because the ReFrame module is still loaded
    prerun_cmds = [
        'module purge',
        'export MANPATH="::"',  # workaround for https://github.com/TACC/Lmod/issues/590
        'export |grep -v "^declare -x _" > env_prerun',
    ]
    postrun_cmds = ['export |grep -v "^declare -x _" > env_postrun']

    @sanity_function
    def assert_output(self):
        return sn.all([
            sn.assert_not_found(r'.', self.stderr, 'no errors'),
            sn.assert_found(r'^No modules loaded$', self.stdout, 'message: No modules loaded'),
            sn.assert_true(filecmp.cmp('env_prerun', 'env_postrun'), 'environment unchanged'),
        ])

@rfm.simple_test
class LmodTestUnload(LmodTestBase):
    descr += ": unload a module"
    toolchain = f'foss/{calc_tcgen(12)}'
    module_unload = 'FFTW/'
    executable = f'module load {toolchain}; module unload {module_unload}; module --terse list'

    @sanity_function
    def assert_output(self):
        return sn.all([
            sn.assert_found(
                r'dependent module\(s\) are not currently loaded', self.stderr, 'dependent modules not loaded'),
            sn.assert_found(rf'^{self.module_unload}', self.stderr, 'module unloaded'),
            sn.assert_found(rf'^{self.toolchain}$', self.stdout, self.toolchain),
            sn.assert_not_found(rf'^{self.module_unload}$', self.stdout, f'{self.module_unload} not found'),
        ])


@rfm.simple_test
class LmodTestCompat(LmodTestBase):
    "try to load multiple versions of the same module"
    tcname = 'foss'
    toolchain1 = f'{tcname}/{calc_tcgen(12)}'
    toolchain2 = f'{tcname}/{calc_tcgen(24)}'
    executable = f'module load {toolchain1}; module load {toolchain2}; module --terse list'

    @sanity_function
    def assert_fail(self):
        msg = f"""\
Lmod has detected the following error: A different version of the '{self.tcname}'
module is already loaded \(see output of 'ml'\).


If you don't understand the warning or error, contact the helpdesk at
hpc@vub.be"""
        return sn.all([
            sn.assert_found(msg, self.stderr, 'error message: Lmod has detected the following error'),
            sn.assert_found(rf'^{self.toolchain1}$', self.stdout, self.toolchain1),
            sn.assert_not_found(rf'^{self.toolchain2}$', self.stdout, f'{self.toolchain2} not found'),
        ])


@rfm.simple_test
class LmodTestOld(LmodTestBase):
    description = "load old module(shows message)"
    months = 36

    @run_after('init')
    def set_descr(self):
        self.descr += f': {self.description}'

    @run_after('init')
    def set_executable(self):
        self.toolchain = f'foss/{calc_tcgen(self.months)}'
        self.executable = f'module load {self.toolchain}'

    @run_after('init')
    def skip_too_old(self):
        self.skip_if(int(self.toolchain[-5:-1]) < OLDEST_TCGEN, 'installed modules are not old enough for this test')

    @sanity_function
    def assert_output(self):
        msg = f"The module {self.toolchain} is rather old. We recommend a newer version. If there is no newer version available, feel free to request one at hpc@vub.be."  # noqa: E501
        msg = msg.replace(' ', '\s+')
        return sn.assert_found(msg, self.stderr)


@rfm.simple_test
class LmodTestNotOld(LmodTestOld):
    description = "load module that is not 'old' (no output)"
    months = 30

    @sanity_function
    def assert_output(self):
        return sn.all([
            sn.assert_not_found(r'.', self.stdout, 'no output'),
            sn.assert_not_found(r'.', self.stderr, 'no errors'),
        ])


@rfm.simple_test
class LmodTestVeryOld(LmodTestOld):
    description = "load very old module (shows warning)"
    months = 48

    @sanity_function
    def assert_output(self):
        msg = f"Lmod Warning: The module {self.toolchain} is old. Please use a newer version. If there is no newer version available, please request one at hpc@vub.be. If you don't understand the warning or error, contact the helpdesk at hpc@vub.be"  # noqa: E501
        msg = msg.replace(' ', '\s+')
        return sn.assert_found(msg, self.stderr)


@rfm.simple_test
class LmodTestHidden(LmodTestBase):
    descr += ": show old module (hidden)"
    months = 36
    toolchain = f'foss/{calc_tcgen(months)}'
    executable = f'module --show-hidden av {toolchain}'

    @run_after('init')
    def skip_too_old(self):
        self.skip_if(int(self.toolchain[-5:-1]) < OLDEST_TCGEN, 'installed modules are not old enough for this test')

    @sanity_function
    def assert_output(self):
        return sn.assert_found(rf'{self.toolchain} \(H\)', self.stdout)


@rfm.simple_test
class LmodTestNonexisting(LmodTestBase):
    descr += ": load nonexisting module"
    executable = "module load DOESNOTEXIST"

    @sanity_function
    def assert_output(self):
        msg = """\
Lmod has detected the following error: The following module\(s\) are unknown:
"DOESNOTEXIST"

Please check the spelling or version number. Also try "module spider ..."
It is also possible your cache file is out-of-date; it may help to try:
  \$ module --ignore_cache load "DOESNOTEXIST"

Also make sure that all modulefiles written in TCL start with the string
#%Module

If you don't understand the warning or error, contact the helpdesk at
hpc@vub.be"""
        return sn.assert_found(msg, self.stderr)


@rfm.simple_test
class LmodTestClusterModule(LmodTestBase):
    descr += ": show + load cluster module"
    module = "cluster/hydra"
    executable = '\n'.join([
        f"module --terse av {module} | grep '^cluster/hydra$' || echo {module} not available",
        f"module load {module}",
        f"module --terse list {module}",
    ])

    @sanity_function
    def assert_output(self):
        return sn.all([
            sn.assert_found(
                rf'{self.module} not available',
                self.stdout,
                'cluster module not available (hidden)'
            ),  # module av
            sn.assert_found(rf'^{self.module} <H>$', self.stdout, self.module),  # module list
        ])


@rfm.simple_test
class LmodTestLoadLmod(LmodTestBase):
    descr += ": load a foss module and check if Lmod (lua) still works"
    toolchain = f'foss/{calc_tcgen(12)}'
    executable = f'module load {toolchain}; module av'

    @sanity_function
    def assert_output(self):
        return sn.all([
            sn.assert_found(rf' foss/{calc_tcgen(12)}', self.stdout, f'foss/{calc_tcgen(12)}'),
            sn.assert_found(r' Python/', self.stdout, 'Python'),
            sn.assert_found(r' R/', self.stdout, 'R'),
            sn.assert_found(
                r'^If you need software that is not listed, request it at hpc@vub.be$',
                self.stdout,
                'message: If you need software that is not listed'
            ),
        ])


@rfm.simple_test
class LmodTestJavaMemory(LmodTestBase):
    descr += ": memory in Java modules"
    executable = '\n'.join([
        'module load Java',
        f'python3 -c "{check_java_memory}"',
        'hostname',
    ])

    @sanity_function
    def assert_output(self):
        return sn.assert_found(r'^True$', self.stdout)


@rfm.simple_test
class LmodTestCachedLoads(LmodTestBase):
    description = ": load a module from spider cache and check for zero exit code"
    lmod_cached_loads = 1

    @run_after('init')
    def set_descr(self):
        self.descr += f': {self.description}'

    @run_after('init')
    def set_executable(self):
        self.executable = f'LMOD_CACHED_LOADS={self.lmod_cached_loads} ml foss/{calc_tcgen(12)}'

    @sanity_function
    def assert_zero_exitcode(self):
        return sn.assert_eq(self.job.exitcode, 0)


@rfm.simple_test
class LmodTestNotCachedLoads(LmodTestCachedLoads):
    description = ": load a module without spider cache and check for zero exit code"
    lmod_cached_loads = 0
