from typing import Optional

import appdirs
import os


class Config:
    REGISTRY_GIT_BRANCH_NAME = 'main'
    DEFAULT_GIT_REMOTE_NAME = 'origin'
    DEFAULT_GIT_BRANCH_NAME = 'main'
    PLUGIN_XML_DIR = "plugins"

    # See https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
    DATE_TIME_DISPLAY_FORMAT = "%x, %X"

    GLOBAL_GRID_PADDING = {'padx': 5, 'pady': 5}

    def __init__(self,
                 naevpm_root: Optional[str] = appdirs.user_data_dir("naev-package-manager"),
                 naev_root: Optional[str] = appdirs.user_data_dir("naev", appauthor=False, roaming=True)):
        super().__init__()

        self.PM_ROOT = naevpm_root
        self.DATABASE = os.path.join(self.PM_ROOT, "naevpm.db")
        self.REGISTRIES = os.path.join(self.PM_ROOT, "registries")
        self.LOCAL_REGISTRY = os.path.join(self.REGISTRIES, 'LOCAL')
        self.PLUGINS_CACHE = os.path.join(self.PM_ROOT, "plugins")

        self.NAEV_ROOT = naev_root
        self.NAEV_PLUGIN_DIR = os.path.join(self.NAEV_ROOT, "plugins")

        if not os.path.exists(self.LOCAL_REGISTRY):
            os.makedirs(self.LOCAL_REGISTRY)
        if not os.path.exists(self.PLUGINS_CACHE):
            os.makedirs(self.PLUGINS_CACHE)
        if not os.path.exists(self.LOCAL_REGISTRY):
            os.makedirs(self.LOCAL_REGISTRY)
