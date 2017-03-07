import re
from jinja2 import contextfunction


@contextfunction
def get_pages_metadata(context, filters=None):
    if not isinstance(filters, dict) and filters:
        raise TypeError('Filters are not a dictionary')

    return_data = []
    for page_name, _format in context['source'].list_pages():
        data, filename = context['source'].read_page(page_name, _format)
        page_data = parse_page_metadata(data, page_name)

        if filter_metadata(filters, page_data) is True:
            return_data.append(page_data)

    return return_data


def parse_page_metadata(data, page):
    page_metadata = {'page': page}
    lines = data.splitlines(True)
    for i, line in enumerate(lines):
        if not re.search(r'^\s*[\w\-]+\s*=', line):
            break
        name, value = line.split('=', 1)
        value = value.strip()
        if value.startswith('[') and value.endswith(']'):
            value = [element.strip() for element in value[1:-1].split(',')]
        page_metadata[name.strip()] = value
    return page_metadata


def filter_metadata(filters, metadata):
    if filters is None:
        return True
    for filter_name, filter_value in filters.items():
        if filter_name not in metadata:
            return False
        if isinstance(metadata[filter_name], list):
            for option in filter_value:
                if str(option) not in metadata[filter_name]:
                    return False
        if filter_value != metadata[filter_name]:
                return False
    return True
