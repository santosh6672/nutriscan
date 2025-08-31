from django import template

register = template.Library()

@register.filter(name='split')
def split_filter(value, delimiter=None):
    """Custom template filter to split a string by a delimiter."""
    if delimiter is None:
        delimiter = ' '
    return value.split(delimiter)

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Custom template filter to get a dictionary item by key."""
    return dictionary.get(key, None)