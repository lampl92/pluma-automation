import math
import os

from farmtest import TestBase, TaskFailed
from farmcore.baseclasses import ConsoleBase


class MemorySize(TestBase):
    def __init__(self, board, total_mb=None, available_mb=None):
        super().__init__(self)
        self.board = board
        self.available_mb = available_mb
        self.total_mb = total_mb

        if not total_mb and not available_mb:
            raise ValueError(f'"total_mb" and/or "available_mb" have to be'
                             'provided for {self}, but none was provided."')

    def test_body(self):
        console = self.board.console
        if not console:
            raise TaskFailed('No console available')

        self.board.login()
        received = console.send_and_read('cat /proc/meminfo')
        available_mb = None
        total_mb = None

        try:
            for line in received.splitlines():
                if line.startswith('MemFree:'):
                    available_mb = math.floor(int(line.split()[1]) / 1024)
                if line.startswith('MemTotal:'):
                    total_mb = math.floor(int(line.split()[1]) / 1024)
        except:
            # Handled just after
            pass

        if not available_mb or not total_mb:
            raise TaskFailed(
                f'Unexpected output from /proc/meminfo:{os.linesep}{received}')

        if self.total_mb and total_mb != self.total_mb:
            raise TaskFailed(
                f'The system has {total_mb} MB of RAM, but expected {self.total_mb} MB')

        if self.available_mb and available_mb < self.available_mb:
            raise TaskFailed(
                f'The system has {available_mb} MB of RAM available, but expected at least {self.available_mb} MB')
