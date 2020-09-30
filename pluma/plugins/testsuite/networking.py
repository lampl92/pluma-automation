import os
import re
import time
import concurrent.futures

from pluma.core.baseclasses import Logger
from pluma.test import ShellTest, TaskFailed
from pluma import Board, HostConsole


log = Logger()


class NetworkingTestBase(ShellTest):
    def __init__(self, board: Board, target: str = None):
        super().__init__(board, script='')

        if not target:
            ssh_console = board.get_console('ssh')
            if not ssh_console:
                raise ValueError(f'{self}: You need to provide a "target" parameter, '
                                 'or an SSH console to get the target host from.')
            target = ssh_console.target

        self.target = target


class RespondsToPing(NetworkingTestBase):
    '''Verifies that there's a response to ping on the target'''
    def __init__(self, board: Board, target: str = None):
        super().__init__(board, target)
        self.run_on_host = True
        self.scripts = [f'ping -c 1 {self.target}']


class IperfBandwidth(NetworkingTestBase):
    '''Verifies the minimum bandwidth (in MBps)'''
    def __init__(self, board: Board, minimum_mbps: float, target: str = None, duration: int = None):
        super().__init__(board, target)
        self.duration = int(duration) if duration else 10
        self.timeout = 10 + self.duration * 1.1
        self.minimum_mbps = float(minimum_mbps)
        # Use `runs_in_shell=False` to disable retcode check
        self.runs_in_shell = False

    def run_iperf_server(self) -> str:
        return self.run_commands(scripts=['iperf -s'])

    def test_body(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            iperf_server = executor.submit(self.run_iperf_server)

            # Wait for the server to start
            time.sleep(2)
            command = f'iperf -c {self.target} --time {self.duration}'
            self.run_commands(console=HostConsole('sh'), scripts=[command])

            target_output = iperf_server.result()

        bandwidth_regex = r'sec\s+(\d+\.\d+) MBytes'
        match = re.search(bandwidth_regex, target_output, re.MULTILINE)
        if not match:
            raise TaskFailed('Failed to match iperf bandwidth regex for '
                             f'output:{os.linesep}{target_output}')

        bandwidth = float(match.group(1))
        if bandwidth < self.minimum_mbps:
            raise TaskFailed('Bandwidth is lower than the minimum expected of '
                             f'{self.minimum_mbps} MBps with {bandwidth} MBps.')

        log.info(f'Bandwidth: {bandwidth} MBps')
