import re

from pluma.test import TestBase, TaskFailed, CommandRunner


class KernelModulesLoaded(TestBase):
    '''Verifies that a set of kernel modules are loaded'''
    def __init__(self, board, modules: list):
        super().__init__(board)

        if not modules:
            raise ValueError('"modules" list cannot be empty')

        if isinstance(modules, str):
            modules = [modules]
        elif not isinstance(modules, list):
            raise ValueError(
                f'"modules" must be a string or a list, but "{modules}" was provided')

        self.modules = modules

    def test_body(self):
        console = self.board.console
        if not console:
            raise TaskFailed('No console available')

        output = CommandRunner.run(test_name=str(
            self), console=console, command='lsmod', timeout=3)

        missing_modules = []
        for module in self.modules:
            found = False
            # For some reason, re.MULTILINE fails to match
            for line in output.splitlines():
                if re.match(fr'^{module}\b', line):
                    found = True
                    break

            if not found:
                missing_modules.append(module)

        if missing_modules:
            raise TaskFailed(
                f'The following kernel modules are not loaded: "{missing_modules}"')
