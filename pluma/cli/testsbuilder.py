import subprocess
from pathlib import Path
import shutil
from pluma.core.baseclasses import Logger

log = Logger()


class TestsBuildError(Exception):
    pass


class TestsBuilder:
    '''Setup and cross-compile C tests with a Yocto SDK.

    Provide a set of methods to install a Yocto SDK, to find and
    source a Yocto SDK environment, and to cross compile a C
    application locally.
    '''
    DEFAULT_BUILD_ROOT = Path().absolute()/'build'
    DEFAULT_TOOLCHAIN_INSTALL_DIR = DEFAULT_BUILD_ROOT/'toolchain'
    DEFAULT_EXEC_INSTALL_DIR = DEFAULT_BUILD_ROOT/'ctests'

    @staticmethod
    def create_directory(directory):
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(
                f'Failed to create build directory {directory}: {e}')

    @staticmethod
    def install_yocto_sdk(yocto_sdk, install_dir=None):
        if not yocto_sdk or not isinstance(yocto_sdk, str):
            raise ValueError('Null Yocto SDK file path provided')

        yocto_sdk = Path(yocto_sdk).absolute()
        if not Path(yocto_sdk).is_file():
            raise TestsBuildError(
                f'Failed to locate Yocto SDK "{yocto_sdk}" for C tests')

        if not install_dir:
            install_dir = TestsBuilder.DEFAULT_TOOLCHAIN_INSTALL_DIR

        install_dir = Path(install_dir).absolute()
        TestsBuilder.create_directory(install_dir)

        log.info('Installing Yocto SDK...')
        log.log([f'SDK: "{yocto_sdk}"',
                 'Destination: "{install_dir}"'])

        try:
            command = [yocto_sdk, '-y', '-d', install_dir]
            subprocess.check_output(command, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise TestsBuildError(
                f'Failed to install Yocto SDK: {e.output.decode()}')

        return str(install_dir)

    @staticmethod
    def find_yocto_sdk_env_file(install_dir):
        '''Search for a Yocto SDK environment file in a folder.'''
        env_file_pattern = 'environment-'
        for file in Path(install_dir).glob('*'):
            if str(file).startswith(env_file_pattern):
                return str((Path(install_dir)/file).absolute())

        raise TestsBuildError(
            f'No environment file ({env_file_pattern}) found in the toolchain installation folder ({install_dir})')

    @staticmethod
    def build_c_test(target_name, env_file, sources, flags=None, install_dir=None):
        '''Cross-compile a C application with a Yocto SDK environment file.'''
        if not target_name or not env_file or not sources:
            raise ValueError('Null target, environment or sources passed')

        if not install_dir:
            install_dir = TestsBuilder.DEFAULT_EXEC_INSTALL_DIR

        if isinstance(sources, list):
            sources = ' '.join(sources)

        if not flags:
            flags = ''
        elif isinstance(flags, list):
            flags = ' '.join(flags)

        install_dir = Path(install_dir).absolute()
        TestsBuilder.create_directory(install_dir)
        target_filepath = Path(install_dir)/target_name

        log.info(f'Cross compiling "{target_name}"...')
        command = f'. {env_file} && $CC {sources} {flags} -o {target_filepath}'
        log.debug(f'Build command = {command}')

        try:
            out = subprocess.check_output(
                command, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise TestsBuildError(
                f'Failed to build "{target_name}": {e.output.decode()}')

        log.debug(f'Build output = {out.decode()}')

        return str(target_filepath)

    @staticmethod
    def clean(force=False):
        '''Clean build files.'''
        try:
            # TODO: Would need to use actual build folder and list of built/installed
            # files
            build_folder = TestsBuilder.DEFAULT_BUILD_ROOT

            if not force:
                answer = input(
                    f'Do you confirm removing build folder "{build_folder}"? [yN]: ')
                if (answer != 'y'):
                    log.log('Aborting clean operation.')
                    return

            if build_folder == '' or build_folder == '/':
                raise TestsBuildError(
                    f'Refusing to clean build folder "{build_folder}"')

            shutil.rmtree(build_folder)
            log.log('Removed toolchain and test build folder')

        except Exception as e:
            raise TestsBuildError(
                f'Failed to clean build output: {e}')
