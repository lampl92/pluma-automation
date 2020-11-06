import json
import os
from typing import List
from copy import deepcopy

from pluma import Board, SerialConsole, SSHConsole, SoftPower, IPPowerPDU
from pluma.cli import Configuration, ConfigurationError, TargetConfigError, \
    PlumaContext
from pluma.core.power import Uhubctl
from pluma.core.baseclasses import Logger, ConsoleBase, PowerBase
from pluma.core.dataclasses import SystemContext, Credentials

log = Logger()


class TargetConfig:
    @staticmethod
    def create_context(config: Configuration) -> PlumaContext:
        if not isinstance(config, Configuration):
            raise ValueError('Invalid configuration: The configuration passed '
                             'should be a Configuration instance.')
        try:
            context = TargetConfig._create_context(config)
        except ConfigurationError as e:
            raise TargetConfigError(e)
        else:
            TargetConfig.print_context_settings(context)
            config.ensure_consumed()
            return context

    @staticmethod
    def _create_context(config: Configuration) -> PlumaContext:
        variables = TargetFactory.parse_variables(config.pop('variables'))
        system = TargetFactory.parse_system_context(config.pop('system'))
        serial, ssh = TargetFactory.create_consoles(config.pop('console'), system)

        if not serial and not ssh:
            log.warning("No console defined in the device configuration file")

        power = TargetFactory.create_power_control(
            config.pop('power'), ssh or serial)

        config.ensure_consumed()

        consoles = {}
        if serial:
            consoles['serial'] = serial
        if ssh:
            consoles['ssh'] = ssh

        board = Board('Test board', console=consoles, power=power,
                      system=system)
        return PlumaContext(board, variables=variables)

    @staticmethod
    def print_context_settings(context: PlumaContext):
        log.log('Components:', bold=True)

        serial = context.board.get_console('serial')
        suffix = 'Default' if serial and context.board.console is serial else None
        TargetConfig.print_component('Serial', serial, suffix)

        ssh = context.board.get_console('ssh')
        suffix = 'Default' if ssh and context.board.console is ssh else None
        TargetConfig.print_component('SSH', ssh, suffix)

        TargetConfig.print_component('Prompt', context.board.system.prompt_regex)
        TargetConfig.print_component('Login', context.board.system.credentials.login)
        TargetConfig.print_component(
            'Password', '******' if context.board.system.credentials.password else None)
        TargetConfig.print_component('Power control', context.board.power)
        TargetConfig.print_component('Storage', context.board.storage)
        TargetConfig.print_component('USB Hub', context.board.hub)
        log.log('')

    @staticmethod
    def print_component(label: str, component, suffix: str = None):
        color = 'green' if component else None

        if suffix:
            log.log(f'    {label}:  {str(component)} - {suffix}', color=color)
        else:
            log.log(f'    {label}:  {str(component)}', color=color)


class TargetFactory:
    @staticmethod
    def parse_variables(variables_config: Configuration) -> dict:
        if not variables_config:
            return {}

        return variables_config.content()

    @staticmethod
    def parse_credentials(credentials_config: Configuration) -> Credentials:
        if not credentials_config:
            return Credentials()

        credentials = Credentials(
            credentials_config.pop('login'),
            credentials_config.pop('password'))
        credentials_config.ensure_consumed()
        return credentials

    @staticmethod
    def parse_system_context(system_config: Configuration) -> SystemContext:
        if not system_config:
            return SystemContext()

        credentials = TargetFactory.parse_credentials(system_config.pop('credentials'))
        system = SystemContext(prompt_regex=system_config.pop('prompt_regex'),
                               credentials=credentials)
        system_config.ensure_consumed()
        return system

    @staticmethod
    def create_consoles(config: Configuration, system: SystemContext) -> List[ConsoleBase]:
        if not config:
            return None, None

        serial = TargetFactory.create_serial(config.pop('serial'), system)
        ssh = TargetFactory.create_ssh(config.pop('ssh'), system)
        config.ensure_consumed()
        return serial, ssh

    @staticmethod
    def create_serial(serial_config: Configuration, system: SystemContext) -> ConsoleBase:
        if not serial_config:
            return None

        log.debug(f'Serial config = {serial_config}')

        port = serial_config.pop('port')
        if not port:
            raise TargetConfigError(
                'Missing "port" attributes for serial console in the configuration file')

        serial = SerialConsole(port=port, baud=int(serial_config.pop('baud') or 115200),
                               system=system)
        serial_config.ensure_consumed()
        return serial

    @staticmethod
    def create_ssh(ssh_config: Configuration, system: SystemContext) -> ConsoleBase:
        if not ssh_config:
            return None

        log.debug('SSH config = ' + json.dumps(ssh_config.content()))
        target = ssh_config.pop('target')
        login = ssh_config.pop('login', system.credentials.login)

        if not target or not login:
            raise TargetConfigError(
                'Missing "target" or "login" attributes for SSH console in the configuration file')

        password = ssh_config.pop('password', system.credentials.password)
        ssh_config.ensure_consumed()

        # Create a new system config to override default credentials
        ssh_system = deepcopy(system)
        ssh_system.credentials.login = login
        ssh_system.credentials.password = password

        return SSHConsole(target, system=ssh_system)

    @staticmethod
    def create_power_control(power_config: Configuration, console: ConsoleBase) -> PowerBase:
        if not power_config:
            power_config = Configuration()

        POWER_SOFT = 'soft'
        POWER_IPPOWER9258 = 'ippower9258'
        POWER_UHUBCTL = 'uhubctl'
        POWER_LIST = [POWER_SOFT, POWER_IPPOWER9258, POWER_UHUBCTL]

        if len(power_config) > 1:
            raise TargetConfigError(
                'Only one power control should be provided in the target configuration,'
                f' but two or more provided:{os.linesep}{power_config}')

        if power_config:
            control_type = power_config.first()
        elif console:
            control_type = POWER_SOFT
        else:
            return None

        if control_type not in POWER_LIST:
            raise TargetConfigError(
                f'Unsupported power control type "{control_type}". Supported types: {POWER_LIST}')

        power_config = power_config.pop(control_type) or Configuration()
        power = None
        if control_type == POWER_SOFT:
            if not console:
                raise TargetConfigError(
                    'No console available for soft power control')

            on_cmd = power_config.pop('on_cmd')
            off_cmd = power_config.pop('off_cmd')
            power = SoftPower(console, on_cmd=on_cmd, off_cmd=off_cmd)

        elif control_type == POWER_IPPOWER9258:
            host = power_config.pop('host')
            outlet = power_config.pop('outlet')
            if not host or not outlet:
                raise TargetConfigError(
                    'IP Power PDU "host" and/or "outlet" attributes are missing')

            port = power_config.pop('port')
            login = power_config.pop('login')
            password = power_config.pop('password')
            power = IPPowerPDU(outlet, host, netport=port,
                               username=login, password=password)
        elif control_type == POWER_UHUBCTL:
            power = Uhubctl(location=power_config.pop('location'),
                            port=power_config.pop('port'))
        else:
            raise Exception('Unreachable, unknown power controller')

        power_config.ensure_consumed()
        return power
