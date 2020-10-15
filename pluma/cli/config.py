import yaml
import json
import os

from pluma.core.baseclasses import Logger
from abc import ABC, abstractmethod

log = Logger()


class ConfigurationError(Exception):
    pass


class TargetConfigError(Exception):
    pass


class TestsConfigError(Exception):
    pass


class Configuration:
    def __init__(self, config: dict = None):
        config = config or {}
        if not isinstance(config, dict):
            raise ValueError('Configuration class requires a "dict" object')

        self.config = config

    def pop(self, attribute, default=None):
        value = self.pop_raw(attribute, default)
        if isinstance(value, dict):
            return Configuration(value)

        return value

    def pop_raw(self, attribute, default=None):
        return self.config.pop(attribute, default)

    def read_and_keep(self, attribute):
        return self.config.get(attribute)

    def __len__(self):
        return len(self.config)

    def first(self):
        for key in self.config:
            return key

    def ensure_consumed(self):
        if len(self) > 0:
            unconsumed_data = self.config
            self.config = {}
            raise ConfigurationError(
                'The following configuration attributes were not recognized or not used:'
                f'{os.linesep}{unconsumed_data}')

    def content(self):
        return self.config

    def __str__(self):
        return json.dumps(self.content())

    def __eq__(self, other):
        return self.content() == other.content()


class TestDefinition():
    '''Data class representing a test, its class, and parameters.'''

    def __init__(self, name: str, testclass: type, test_provider: object,
                 parameter_sets: list = None, selected: bool = False):
        if not name or name == '':
            raise ValueError('Test name cannot be empty')

        if not testclass or not test_provider:
            raise ValueError('Test class and test provider must be set')

        self.name = name
        self.testclass = testclass
        self.provider = test_provider
        self.parameter_sets = parameter_sets or []
        self.selected = selected

        if isinstance(self.parameter_sets, dict):
            self.parameter_sets = [self.parameter_sets]
        elif not isinstance(self.parameter_sets, list):
            raise ValueError(
                f'Parameter sets for test "{name}" should be a list of dictionaries')

    def __repr__(self):
        return f'{self.__module__}.{self.__class__.__name__}{self.parameter_sets or ""}'

    def description(self):
        desc = self.testclass.__doc__

        return desc


class TestsProvider(ABC):
    '''Abstract base class that provides TestDefinition from the configuration

    Classes implementing TestsProvider must provide a unique configuration key
    (configuration_key), and the "all_tests", which returns the list of
    TestDefinition from a configuration.
    '''
    @abstractmethod
    def display_name(self) -> str:
        '''Return a human-friendly name for the provider'''

    @abstractmethod
    def configuration_key(self) -> str:
        '''Return a unique key (string) representing the provider.

        If the configuration key is encountered in the test configuration,
        this provider will be used when creating the tests definition by
        calling "all_tests" and "selected_tests".
        '''

    @abstractmethod
    def all_tests(self, key: str, config: Configuration) -> list:
        '''Return all TestDefinition from the "config" provided by the sequence key "key"'''


class ConfigPreprocessor(ABC):
    @abstractmethod
    def preprocess(self, raw_config: str) -> str:
        '''Return an updated configuration from raw text'''
        pass


class PlumaConfig:
    @staticmethod
    def load_configuration(name: str, config_path: str,
                           preprocessor: ConfigPreprocessor = None) -> Configuration:
        return Configuration(PlumaConfig.load_yaml(name, config_path, preprocessor))

    @staticmethod
    def load_yaml(name: str, yaml_file_path: str,
                  preprocessor: ConfigPreprocessor = None) -> dict:
        try:
            with open(yaml_file_path, 'r') as config:
                content = config.read()
                if preprocessor:
                    content = preprocessor.preprocess(content)

                return yaml.load(content, Loader=yaml.FullLoader)
        except FileNotFoundError as e:
            raise ConfigurationError(
                f'{name} "{yaml_file_path}" does not exist') from e
        except yaml.parser.ParserError as e:
            raise ConfigurationError(
                f'Error while parsing {name} "{yaml_file_path}":'
                f'{os.linesep}{e}') from e
        except Exception as e:
            raise ConfigurationError(
                f'An error occurred while opening/parsing {name} "{yaml_file_path}":'
                f'{os.linesep}{e}') from e
