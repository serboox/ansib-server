import yaml


class _ConfigGroup(dict):

    def __init__(self, group_name, **kwargs):
        super(_ConfigGroup, self).__init__(**kwargs)
        self.__dict__.update(kwargs)
        self._name = group_name

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            raise AttributeError('No "{0}.{1}" config option'.format(
                self._name, attr))


class _ConfigDict(object):
    """Proxy around dict. It allows you do some of the dict things.

    >>> config['item'] = 1
    >>> config.get('item', 1)

    and also nice syntactic sugar like this:

    >>> config.item
    >>> config.item = 1
    """

    def __init__(self):
        self.set_items({})

    def clear(self):
        """Remove all items from config dict."""
        self.set_items({})

    @property
    def items(self):
        """All items in the config dict."""
        return self._items

    def set_items(self, items):
        """Set config dict. Useful for initialization."""
        object.__setattr__(self, '_items', items)

    def __getattr__(self, name):
        return self._get(name)

    def __getitem__(self, key):
        return self._get(key)

    def _get(self, key):
        try:
            result = self._items[key]
        except KeyError:
            raise KeyError('No "{0}" config option.'.format(key))
        if isinstance(result, dict):
            return _ConfigGroup(group_name=key, **result)
        return result

    def get(self, name, default=None):
        """Similar to dict.get return element from config or just def val."""
        return self._items.get(name, default)

    def __setattr__(self, name, value):
        self._items[name] = value

    def __setitem__(self, key, value):
        self._items[key] = value


CONF = _ConfigDict()


def init_app(config_path, **kwargs):
    """Load YAML config from the specified path and init proxy wrapper."""
    items = yaml.safe_load(open(config_path))
    CONF.set_items(items)
