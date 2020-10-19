import subprocess
import os.path
import sys
import shutil

from typing import List

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
    DEFAULT_BUILD_ROOT = os.path.join(os.path.dirname(
        os.path.abspath(sys.modules['__main__'].__file__)), 'build')
    DEFAULT_TOOLCHAIN_INSTALL_DIR = os.path.join(
        DEFAULT_BUILD_ROOT, 'toolchain')
    DEFAULT_EXEC_INSTALL_DIR = os.path.join(DEFAULT_BUILD_ROOT, 'ctests')

    @staticmethod
    def create_directory(directory: str):
        '''Create the directory or raise an error'''
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            raise ValueError(
                f'Failed to create build directory {directory}: {e}')

    @staticmethod
    def install_yocto_sdk(yocto_sdk: str, install_dir: str = None) -> str:
        '''Install the Yocto SDK in a directory and return the directory used'''
        if not yocto_sdk or not isinstance(yocto_sdk, str):
            raise ValueError('Null Yocto SDK file path provided')

        yocto_sdk = os.path.abspath(yocto_sdk)
        if not os.path.isfile(yocto_sdk):
            raise TestsBuildError(
                f'Failed to locate Yocto SDK "{yocto_sdk}" for C tests')

        if not install_dir:
            install_dir = TestsBuilder.DEFAULT_TOOLCHAIN_INSTALL_DIR

        install_dir = os.path.abspath(install_dir)
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

        return install_dir

    @staticmethod
    def get_yocto_sdk_env_file(install_dir: str) -> str:
        '''Return the path to the Yocto SDK environment file in a folder or raise an error.'''
        env_file_pattern = 'environment-'
        for file in os.listdir(install_dir):
            if file.startswith(env_file_pattern):
                return os.path.abspath(os.path.join(install_dir, file))

        raise TestsBuildError(
            f'No environment file ({env_file_pattern}) found in the toolchain '
            f'installation folder ({install_dir})')

    @staticmethod
    def build_c_test(target_name: str, env_file: str, sources: List[str],
                     flags: List[str] = None, install_dir: str = None) -> str:
        '''Cross-compile a C application with a Yocto SDK environment file and return its path'''
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

        install_dir = os.path.abspath(install_dir)
        TestsBuilder.create_directory(install_dir)
        target_filepath = os.path.join(install_dir, target_name)

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

        return target_filepath

    @staticmethod
    def clean(force: bool = False):
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
