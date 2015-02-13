"""Read config files from environment.

Use /adama/defaults.yml as the default values.

"""

from typing import List, Dict, cast, Union, typevar

import os

import yaml


class EnvironDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.defaults = yaml.load(open('/adama/defaults.yml')) or {}

    def __getattr__(self, attr):
        return os.environ.get(attr, self.defaults.get(attr))


Config = EnvironDict()
