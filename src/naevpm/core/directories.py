import appdirs
import os


class Directories:
    PM_ROOT = appdirs.user_data_dir("naev-package-manager")
    DATABASE = os.path.join(PM_ROOT, "naevpm.db")
    REGISTRIES = os.path.join(PM_ROOT, "registries")
    PLUGINS_CACHE = os.path.join(PM_ROOT, "plugins")

    NAEV_ROOT = appdirs.user_data_dir("naev")
    NAEV_PLUGIN_DIR = os.path.join(NAEV_ROOT, "plugins")


def init_directories():
    os.makedirs(Directories.REGISTRIES, exist_ok=True)
