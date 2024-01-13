import locale
import logging
from datetime import datetime, timezone
import click
from tabulate import tabulate

from naevpm.core import models
from naevpm.core.abstract_thread_communication import AbstractCommunication
from naevpm.core.application_logic import ApplicationLogic, ApplicationLogicRegistrySourceWasAlreadyAdded, \
    ApplicationLogicEmptyRegistrySource
from naevpm.core.config import Config
from naevpm.core.models import IndexedPluginDbModel, RegistryDbModel
from naevpm.core.sqlite_database_connector import SqliteDatabaseConnector
from naevpm.gui import display_utils
from naevpm.gui.data_model_to_str_list import registry_to_str_list, plugin_to_str_list

config = Config()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
database_connector = SqliteDatabaseConnector(config.DATABASE)
logic = ApplicationLogic(database_connector, config)


class Communication(AbstractCommunication):

    def message(self, msg: str, delay: bool = False):
        super().message(msg, delay)
        logger.info(msg)


comm = Communication()


def reminders():
    registry_update_reminder()


def registry_update_reminder():
    # Remind the player to update their registries once in a while.
    registries = logic.get_registries()
    for r in registries:
        last_fetched = r.last_fetched
        if last_fetched is None:
            continue
        now = datetime.now(timezone.utc)
        delta = now - last_fetched

        if delta.days >= 7:
            logger.info("It has been more than 7 days since you last updated your local package registry.")
            logger.info("To update, run naevpm registry update. Updating is recommended to keep")
            logger.info("up to date on the latest plugins for Naev.")


@click.group()
def root():
    reminders()
    pass


@root.group()
def registry():
    pass


def create_plugin_table(plugins: list[IndexedPluginDbModel]):
    table = []
    for p in plugins:
        table.append(plugin_to_str_list(p))
    return table


def create_registry_table(registries: list[RegistryDbModel]):
    table = []
    for r in registries:
        table.append(registry_to_str_list(r))
    return table


@registry.command("list")
def registry_list():
    registries = logic.get_registries()
    print(tabulate(create_registry_table(registries),
                   headers=[display_utils.field_name_as_list_header(field) for field in models.registry_fields]))


@registry.command("fetch")
@click.argument("source")
def registry_fetch(source: str):
    r = database_connector.get_registry(source.strip())
    if r is None:
        logger.warning('Could not fetch as registry is not added')
    else:
        logic.fetch_registry_plugin_metadatas(r, comm)


@registry.command("fetch-all")
def registry_fetch():
    registries = database_connector.get_registries()
    for r in registries:
        logic.fetch_registry_plugin_metadatas(r, comm)


@registry.command("add")
@click.argument("source")
def registry_add(source: str):
    if source not in TRUSTED:
        logger.warning(UNTRUSTED_WARNING)
    try:
        logic.add_registry(source.strip(), comm)
    except ApplicationLogicRegistrySourceWasAlreadyAdded:
        logger.warning("Already added")
    except ApplicationLogicEmptyRegistrySource:
        logger.warning("Empty source")


@registry.command("remove")
@click.argument("source")
def registry_add(source: str):
    r = logic.get_registry(source.strip())
    if r is not None:
        logic.remove_registry(r, comm)


# https://github.com/naev/naev-plugins is the only trusted
# plugin registry. Players are free to add other registries
# but will receive a warning.
TRUSTED = ["https://github.com/naev/naev-plugins"]
UNTRUSTED_WARNING = """\
Warning: Naev does not sandbox any plugin code run on the system. Be careful when installing
unknown plugins, as they may contain malware that could seriously harm your system.

https://github.com/naev/naev-plugins is a curated list, and all plugins submitted there
are subject to manual human review to prevent malicious or offensive plugins.\
"""


@root.group()
def plugin():
    pass


@plugin.command(name='list')
def plugin_list():
    plugins = logic.get_plugins()
    print(tabulate(create_plugin_table(plugins),
                   headers=[display_utils.field_name_as_list_header(field) for field in models.indexed_plugin_fields]))


@plugin.command('delete')
@click.argument("source")
def plugin_delete(source: str):
    p = logic.get_plugin(source)
    if p is None:
        logger.warning('Plugin is not in index')
    else:
        try:
            logic.delete_plugin(p, comm)
        except AssertionError:
            logger.error(f'Operation invalid for state {p.state.name} of plugin.')


@plugin.command('fetch')
@click.argument("source")
def plugin_fetch(source: str):
    p = logic.get_plugin(source)
    if p is None:
        logger.warning('Plugin is not in index')
    else:
        try:
            logic.fetch_plugin(p, comm)
        except AssertionError:
            logger.error(f'Operation invalid for state {p.state.name} of plugin.')


@plugin.command('install')
@click.argument("source")
def plugin_install(source: str):
    p = logic.get_plugin(source)
    if p is None:
        logger.warning('Plugin is not in index')
    else:
        try:
            logic.install_plugin(p, comm)
        except AssertionError:
            logger.error(f'Operation invalid for state {p.state.name} of plugin.')


@plugin.command('remove')
@click.argument("source")
def plugin_remove(source: str):
    p = logic.get_plugin(source)
    if p is None:
        logger.warning('Plugin is not in index')
    else:
        try:
            logic.remove_plugin(p, comm)
        except AssertionError:
            logger.error(f'Operation invalid for state {p.state.name} of plugin.')


@plugin.command('uninstall')
@click.argument("source")
def plugin_uninstall(source: str):
    p = logic.get_plugin(source)
    if p is None:
        logger.warning('Plugin is not in index')
    else:
        try:
            logic.uninstall_plugin(p, comm)
        except AssertionError:
            logger.error(f'Operation invalid for state {p.state.name} of plugin.')


@plugin.command('update')
@click.argument("source")
def plugin_update(source: str):
    p = logic.get_plugin(source)
    if p is None:
        logger.warning('Plugin is not in index')
    else:
        try:
            logic.update_plugin(p, comm)
        except AssertionError:
            logger.error(f'Operation invalid for state {p.state.name} of plugin.')


@plugin.command('check-for-update')
@click.argument("source")
def plugin_check_for_update(source: str):
    p = logic.get_plugin(source)
    if p is None:
        logger.warning('Plugin is not in index')
    else:
        try:
            logic.check_plugin(p, comm)
        except AssertionError:
            logger.error(f'Operation invalid for state {p.state.name} of plugin.')


@plugin.command('check-all-for-update')
def plugin_check_for_update():
    plugins = logic.get_plugins()
    for p in plugins:
        if p.state == models.PluginState.INSTALLED:
            logic.check_plugin(p, comm)


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')

    root()
