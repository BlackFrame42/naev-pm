from datetime import datetime
from enum import Enum
from typing import Optional
import inspect


class PluginMetaDataModel:
    name: Optional[str]
    author: Optional[str]
    version: Optional[str]
    description: Optional[str]
    compatibility: Optional[str]
    priority: Optional[int]
    source: Optional[str]
    blacklist: Optional[list[str]]
    total_conversion: Optional[bool]
    whitelist: Optional[list[str]]

    def __init__(self,
                 name: Optional[str] = None,
                 author: Optional[str] = None,
                 version: Optional[str] = None,
                 description: Optional[str] = None,
                 compatibility: Optional[str] = None,
                 priority: Optional[int] = None,
                 source: Optional[str] = None,
                 blacklist: Optional[list[str]] = None,
                 total_conversion: Optional[bool] = None,
                 whitelist: Optional[list[str]] = None
                 ):
        super().__init__()
        self.name = name
        self.author = author
        self.version = version
        self.description = description
        self.compatibility = compatibility
        self.priority = priority
        self.source = source
        self.blacklist = blacklist
        self.total_conversion = total_conversion
        self.whitelist = whitelist


class RegistryPluginMetaDataModel:
    name: str
    author: Optional[str]
    source: str
    license: Optional[str]
    website: Optional[str]

    # noinspection PyShadowingBuiltins
    def __init__(self,
                 name: str,
                 git: str,
                 author: Optional[str] = None,
                 license: Optional[str] = None,
                 website: Optional[str] = None,
                 ):
        super().__init__()
        self.name = name
        self.source = git
        self.author = author
        self.license = license
        self.website = website


class PluginState(Enum):
    INDEXED = 0
    CACHED = 1
    INSTALLED = 2


class PluginDbModel:
    name: str
    author: Optional[str]
    source: str
    state: PluginState
    license: Optional[str]
    website: Optional[str]
    update_available: Optional[bool]
    registry_source: Optional[str]

    # noinspection PyShadowingBuiltins
    def __init__(self,
                 name: str,
                 source: str,
                 state: PluginState,
                 author: Optional[str] = None,
                 license: Optional[str] = None,
                 website: Optional[str] = None,
                 update_available: Optional[bool] = None,
                 registry_source: Optional[str] = None
                 ):
        super().__init__()
        self.name = name
        self.source = source
        self.state = state
        self.author = author
        self.license = license
        self.website = website
        self.update_available = update_available
        self.registry_source = registry_source


class RegistryDbModel:
    source: str

    last_fetched: Optional[datetime]

    # branch: str

    def __init__(self, source: str, last_fetched: Optional[datetime] = None):
        super().__init__()
        self.source = source
        self.last_fetched = last_fetched


plugin_fields = list(inspect.get_annotations(PluginDbModel))
registry_fields = list(inspect.get_annotations(RegistryDbModel))
