"""
Created on : 2024-07-13
Created by : Mythezone
Updated by : Mythezone
Email      : mythezone@gmail.com
FileName   : ~/project/simlob-refined/config/config.py
Description: Configuration Class
---
Updated    : 
---
Todo       : 
"""

# Insert the path into sys.path for importing.
import sys,os,json
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from .single import SingletonMeta
from types import SimpleNamespace

class ConfigManager(metaclass=SingletonMeta):
    def __init__(self, config_dir='./'):
        if config_dir:
            self.load_config(config_dir)

    def load_config(self, config_dir):
        config_path = os.path.join(config_dir, 'config.json')
        if os.path.isfile(config_path):
            with open(config_path, 'r') as config_file:
                config_data = json.load(config_file)
                self._update_attributes(config_data)
        else:
            raise FileNotFoundError(f"No config.json found in {config_dir}")

    def _update_attributes(self, config_data, prefix=''):
        for key, value in config_data.items():
            if isinstance(value, dict):
                self._update_attributes(value, prefix + key + '.')
            else:
                attribute_name = prefix + key
                self._set_nested_attribute(attribute_name, value)

    def _set_nested_attribute(self, attribute_name, value):
        parts = attribute_name.split('.')
        obj = self
        for part in parts[:-1]:
            if not hasattr(obj, part):
                setattr(obj, part, SimpleNamespace())
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)

    def __getattr__(self, name):
        raise AttributeError(f"Attribute '{name}' not found")

# Usage example
if __name__ == "__main__":
    # Initialize the ConfigManager with the directory containing config.json
    config_manager = ConfigManager()

    # Example of how to access configuration values
    print(f"Database URL: {config_manager.trunk_length}")
    # print(f"API Key: {config_manager.api_key}")

    # Accessing nested configuration values
    # Assuming config.json has a nested structure like {"database": {"host": "localhost", "port": 27017}}
    print(f"Database Host: {config_manager.database.url}")
    print(f"Database Port: {config_manager.database.name}")
    print(f"Database Port: {type(config_manager.folders)}")