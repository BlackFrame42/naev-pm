from datetime import datetime
from typing import Optional

from naevpm.core.config import Config


def display_last_datetime(last: Optional[datetime]) -> str:
    if last is not None:
        # convert to local time zone and stringify with local format
        return str(last.astimezone().strftime(Config.DATE_TIME_DISPLAY_FORMAT))
    else:
        return 'never'


def field_name_as_list_header(field_name: str) -> str:
    return field_name.capitalize().replace('_', ' ')


def display_boolean(v: bool) -> str:
    return 'True' if v else 'False'
