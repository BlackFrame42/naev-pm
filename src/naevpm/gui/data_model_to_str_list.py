from naevpm.core import models
from naevpm.core.models import PluginDbModel, RegistryDbModel
from naevpm.gui import display_utils


def registry_to_str_list(registry: RegistryDbModel) -> list[str]:
    obj = registry.__dict__
    row = []
    for registry_field in models.registry_fields:
        if registry_field == 'last_fetched':
            value = display_utils.display_last_datetime(obj[registry_field])
        else:
            value = obj[registry_field]
        if value is None:
            value = ''
        row.append(value)
    return row


def plugin_to_str_list(plugin: PluginDbModel) -> list[str]:
    obj = plugin.__dict__
    row = []
    for field in models.plugin_fields:
        if field == 'installed' or \
                field == 'cached' or \
                field == 'update_available':
            value = display_utils.display_boolean(obj[field])
        elif field == 'state':
            value = plugin.state.name
        else:
            value = obj[field]
        if value is None:
            value = ''
        row.append(value)
    return row
