import os
import setuptools
import subprocess
import sys


def git_is_installed():
    try:
        subprocess.check_call(['which', 'git'], stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return False
    else:
        return True


def get_version():
    ''' Find the current pluma version from git tags using git-describe '''
    if not git_is_installed():
        raise EnvironmentError(
            '\n\nThe tool "git" must be installed on the system to install '
            'this package.\n'
            'See: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git\n'
        )

    try:
        version = subprocess.check_output(
            ['git', 'describe', '--tags', '--always', '--match', 'v*.*.*'])
        version = version.decode('utf-8').strip()
    except Exception as e:
        version = None
        print('Failed to read Git version, possibly because not .git repository'
              f' is present in this folder. Falling back to "{version}".{os.linesep*2}{str(e)}')
    finally:
        return version


readme_file = 'README.md'
long_description = None
long_description_content_type = None
with open(readme_file, 'r') as fh:
    long_description = fh.read()
    long_description_content_type = 'text/markdown'

requires = [
    'pyserial',
    'setuptools',
    'pyudev',
    'pexpect>=4.6',
    'pyftdi',
    'pyroute2',
    'pandas',
    'pygal',
    'cairosvg',
    'graphviz',
    'nanocom',
    'requests',
    'pytest',
    'pytest-xdist',
    'coverage',
    'pyyaml>=5.1',
    'deprecated'
]

# dataclasses backport for 3.6
if sys.version_info[:2] == (3, 6):
    requires.append('dataclasses')

setuptools.setup(
    name='pluma-automation',
    version=get_version(),
    author='Witekio',
    author_email='mwebster@witekio.com',
    description='Pluma Automation',
    long_description=long_description,
    long_description_content_type=long_description_content_type,
    url='https://github.com/Witekio/pluma-automation/',
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': ['pluma=pluma.__main__:main'],
    },
    python_requires='>=3.6',
    install_requires=requires,
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Development Status :: 3 - Alpha'
    ],
)
