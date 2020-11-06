import copy
import pytest

from pluma.core.dataclasses import SystemContext
from pluma.cli import TargetConfig, TargetFactory, TargetConfigError, \
    Configuration, Credentials, ConfigurationError
from pluma import IPPowerPDU, SoftPower


def test_TargetConfig_create_context_should_work_with_minimal_config(target_config):
    TargetConfig.create_context(Configuration(target_config))


def test_TargetConfig_create_context_should_error_on_unconsumed(target_config):
    invalid_config = target_config
    invalid_config['abc'] = 'value'

    with pytest.raises(TargetConfigError):
        TargetConfig.create_context(Configuration(invalid_config))


def test_TargetConfig_create_context_passes_serial_console_to_create_power_control(serial_config):
    config = Configuration({'console': {'serial': serial_config}})
    context = TargetConfig.create_context(config)
    assert context.board.power is not None


def test_TargetFactory_parse_credentials():
    login = 'abc'
    password = 'def'
    config = Configuration({
        'login': login,
        'password': password
    })

    creds = TargetFactory.parse_credentials(config)
    assert creds.login == login
    assert creds.password == password


def test_TargetFactory_parse_credentials_should_work_with_empty_config():
    creds = TargetFactory.parse_credentials(Configuration())
    assert creds.login == 'root'
    assert creds.password is None


def test_TargetFactory_create_serial(serial_config):
    port = serial_config['port']
    baudrate = serial_config['baud']
    config = Configuration(copy.deepcopy(serial_config))

    console = TargetFactory.create_serial(config, SystemContext())
    assert console.port == port
    assert console.baud == baudrate


def test_TargetFactory_create_serial_should_return_none_with_no_config():
    assert TargetFactory.create_serial(None, None) is None


def test_TargetFactory_create_serial_should_error_with_no_port(serial_config):
    serial_config['other'] = 'abc'

    with pytest.raises(ConfigurationError):
        TargetFactory.create_serial(Configuration(serial_config), SystemContext())


def test_TargetFactory_create_serial_should_error_if_uncomsuned():
    config = Configuration({'baud': 123})

    with pytest.raises(TargetConfigError):
        TargetFactory.create_serial(config, SystemContext())


def test_TargetFactory_create_ssh(ssh_config):
    target = ssh_config['target']
    login = ssh_config['login']
    config = Configuration(copy.deepcopy(ssh_config))

    console = TargetFactory.create_ssh(config, SystemContext())
    assert console.target == target
    assert console.system.credentials.login == login
    assert console.system.credentials.password is None


def test_TargetFactory_create_ssh_should_use_password(ssh_config):
    password = 'pass'
    ssh_config['password'] = password

    console = TargetFactory.create_ssh(Configuration(ssh_config), SystemContext())
    assert console.system.credentials.password == password


def test_TargetFactory_create_ssh_should_default_to_credentials(ssh_config):
    ssh_config.pop('login')

    credslogin = 'credslogin'
    credspassword = 'credspass'

    system = SystemContext(credentials=Credentials(credslogin, credspassword))
    console = TargetFactory.create_ssh(Configuration(ssh_config), system)
    assert console.system.credentials.login == credslogin
    assert console.system.credentials.password == credspassword


def test_TargetFactory_create_ssh_should_prefer_ssh_credentials(ssh_config):
    sshlogin = ssh_config['login']
    sshpassword = 'sshpass'
    ssh_config['password'] = sshpassword

    credslogin = 'credslogin'
    credspassword = 'credspass'

    system = SystemContext(credentials=Credentials(credslogin, credspassword))
    console = TargetFactory.create_ssh(Configuration(ssh_config), system)
    assert console.system.credentials.login == sshlogin
    assert console.system.credentials.password == sshpassword


def test_TargetFactory_create_power_control_should_return_none_with_no_console():
    power = TargetFactory.create_power_control(power_config=None, console=None)
    assert power is None


def test_TargetFactory_create_power_control_should_default_to_SoftPower(mock_console):
    power = TargetFactory.create_power_control(None, mock_console)
    assert isinstance(power, SoftPower)


def test_TargetFactory_create_power_control_should_create_ipp9258(mock_console):
    host = 'hosttest'
    outlet = 3
    login = 'logintest'
    password = 'passwordtest'

    ipp_config = Configuration({
        'ippower9258': {
            'host': host,
            'outlet': outlet,
            'login': login,
            'password': password}
    })

    power = TargetFactory.create_power_control(ipp_config, mock_console)
    assert isinstance(power, IPPowerPDU)
    assert power.host == host
    assert power.port == outlet
    assert power.username == login
    assert power.password == password


def test_TargetFactory_parse_variables_should_allow_variables_access():
    var1 = 'abc'
    var1_value = 'def'
    var2 = 'def'
    var2_value = 3

    variables = TargetFactory.parse_variables(variables_config=Configuration({var1: var1_value,
                                                                              var2: var2_value}))
    assert variables.get(var1) == var1_value
    assert variables.get(var2) == var2_value
