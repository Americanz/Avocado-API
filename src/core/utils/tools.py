import datetime
import re
import time

# from bson import ObjectId
import orjson

LAYOUT_PREFIX = 'layout.'
VIEW_PREFIX = 'view.'
FIRST_LEVEL_ROUTE_COMPONENT_SPLIT = '$'


def check_url(url: str = "/api/v1/system-manage/roles/{role_id}/buttons", url2: str = "/api/v1/system-manage/roles/1/buttons") -> bool:
    pattern = re.sub(r'\{.*?}', '[^/]+', url)
    if re.match(pattern, url2):
        return True
    return False


def get_layout_and_page(component=None):
    layout = ''
    page = ''

    if component:
        layout_or_page, page_item = component.split(FIRST_LEVEL_ROUTE_COMPONENT_SPLIT)
        layout = get_layout(layout_or_page)
        page = get_page(page_item or layout_or_page)

    return layout, page


def get_layout(layout):
    return layout.replace(LAYOUT_PREFIX, '') if layout.startswith(LAYOUT_PREFIX) else ''


def get_page(page):
    return page.replace(VIEW_PREFIX, '') if page.startswith(VIEW_PREFIX) else ''


def transform_layout_and_page_to_component(layout, page):
    if layout and page:
        return f"{LAYOUT_PREFIX}{layout}{FIRST_LEVEL_ROUTE_COMPONENT_SPLIT}{VIEW_PREFIX}{page}"
    elif layout:
        return f"{LAYOUT_PREFIX}{layout}"
    elif page:
        return f"{VIEW_PREFIX}{page}"
    else:
        return ''


def get_route_path_by_route_name(route_name):
    return f"/{route_name.replace('_', '/')}"


def get_path_param_from_route_path(route_path):
    path, param = route_path.split('/:')
    return path, param


def get_route_path_with_param(route_path, param):
    if param.strip():
        return f"{route_path}/:{param}"
    else:
        return route_path


def camel_case_convert(data: dict):
    """
    Convert dictionary keys to lower camel case
    :param data:
    :return:
    """
    converted_data = {}
    for key, value in data.items():
        converted_key = ''.join(word.capitalize() if i else word for i, word in enumerate(key.split('_')))
        converted_data[converted_key] = value
        # converted_data[to_snake_case(key)] = value
    return converted_data


def snake_case_convert(data: dict):
    """
    Convert dictionary keys to underscore format
    :param data:
    :return:
    """
    converted_data = {}
    for key, value in data.items():
        converted_data[to_snake_case(key)] = value
    return converted_data


def to_snake_case(x):
    """
    CamelCase to Underscore Naming
    :param x:
    :return:
    """
    return re.sub(r'(?<=[a-z])[A-Z]|(?<!^)[A-Z](?=[a-z])', '_\\g<0>', x).lower()


def to_camel_case(x):
    """
    Convert the name to camelCase, keep the first word unchanged, and capitalize the first letter of other words, userLoginCount
    :param x:
    :return:
    """
    return re.sub('_([a-zA-Z])', lambda m: (m.group(1).upper()), x)


def to_upper_camel_case(x):
    """
    Convert to upper camel case, capitalize the first letter of all words, userLoginCount
    :param x:
    :return:
    """
    s = re.sub('_([a-zA-Z])', lambda m: (m.group(1).upper()), x)
    return s[0].upper() + s[1:]


def to_lower_camel_case(x):
    """
    Convert to camelCase, lowercase the first letter of the first word, uppercase the first letter of other words, userLoginCount
    :param x:
    :return:
    """
    s = re.sub('_([a-zA-Z])', lambda m: (m.group(1).upper()), x)
    return s[0].lower() + s[1:]


# Here you can handle some formats that cannot be handled originally (ObjectId) or custom display formats (datetime)
def _default(obj):
    if isinstance(obj, datetime.datetime):
        if obj != obj:
            return None
        if obj.hour == 0 and obj.minute == 0:
            return obj.strftime("%Y-%m-%d")
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(obj, datetime.date):
        return obj.isoformat()
    # elif isinstance(obj, ObjectId):
    #     return obj.__str__()
    elif hasattr(obj, "asdict"):
        return obj.asdict()
    elif hasattr(obj, "_asdict"):  # namedtuple
        return obj._asdict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        raise TypeError(f"Unsupported json dump type: {type(obj)}")


def orjson_dumps(data):
    # The styles here are superimposed by |. In fact, each one corresponds to a number. For more styles, see the github link above
    option = orjson.OPT_PASSTHROUGH_DATETIME | orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_INDENT_2
    rv = orjson.dumps(data, default=_default, option=option)
    # rv = orjson.dumps(data, default=_default)
    return rv.decode(encoding='utf-8')


def timestamp_to_time(timestamp):
    time_struct = time.localtime(timestamp)
    time_string = time.strftime("%Y-%m-%d %H:%M:%S", time_struct)
    return time_string


def time_to_timestamp(dt="2023-06-01 00:00:00"):
    timeArray = time.strptime(dt, "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(timeArray)
    return str(int(timestamp))
