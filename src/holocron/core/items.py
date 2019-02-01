"""Wrappers for pipeline items."""

import collections.abc
import itertools
import inspect
import os
import urllib.parse


class Item(collections.abc.MutableMapping):
    """General pipeline item wrapper."""

    def __init__(self, *mappings, **properties):
        self._mapping = {}

        # The only reason behind this constraint is to mimic built-in dict
        # behaviour. Anyway, passing more than one mapping to '__init__' makes
        # no sense and adds confusion.
        if len(mappings) > 1:
            raise TypeError("expected at most 1 argument, got 2")

        for mapping in itertools.chain(mappings, (properties,)):
            self._mapping.update(mapping)

    def __getitem__(self, key):
        try:
            return self._mapping[key]
        except KeyError:
            pass

        try:
            prop = vars(self.__class__)[key]
        except KeyError:
            pass
        else:
            if not key.startswith("_") and (
                    inspect.isdatadescriptor(prop)
                    or inspect.ismethoddescriptor(prop)):
                return getattr(self, key)

        raise KeyError("'%s'" % key)

    def __setitem__(self, key, value):
        self._mapping[key] = value

    def __delitem__(self, key):
        del self._mapping[key]

    def __iter__(self):
        return iter(self.as_mapping())

    def __len__(self):
        return len(self.as_mapping())

    def as_mapping(self):
        return dict(
            {
                key: value.__get__(self)
                for key, value in vars(self.__class__).items()
                if not key.startswith("_") and (
                    inspect.isdatadescriptor(value)
                    or inspect.ismethoddescriptor(value))
            },
            **self._mapping)

    def __eq__(self, other):
        if not isinstance(other, Item):
            return NotImplemented
        return self.as_mapping() == other.as_mapping()


class WebSiteItem(Item):
    """Pipeline item wrapper for a static web site."""

    def __init__(self, *mappings, **properties):
        super(WebSiteItem, self).__init__(*mappings, **properties)

        missing = {"destination", "baseurl"} - self.keys()
        if missing:
            raise TypeError(
                "WebSiteItem is missing some required properties: %s"
                % ", ".join(("'%s'" % prop for prop in sorted(missing))))

    @property
    def url(self):
        destination = self["destination"]

        # Most modern HTTP servers serve 'index.html' implicitly if a URL
        # that points to a directory is requested. Since we want to produce
        # beautiful URLs, we strip 'index.html' away from a URL.
        if os.path.basename(destination) in ("index.html", "index.htm"):
            destination = os.path.dirname(destination) + "/"

        return urllib.parse.quote("/" + destination)

    @property
    def absurl(self):
        # Since 'url' property always comes with a leading '/' character,
        # there's a need to strip a trailing '/' character away from 'baseurl'
        # property to prevent doubled '/' after concatenation.
        return self["baseurl"].rstrip("/") + self.url
