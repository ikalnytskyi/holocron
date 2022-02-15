"""Parse YAML front matter and set its values as item"s properties."""

import collections.abc
import re

import toml
import yaml

from ._misc import parameters

_DELIMITERS = {
    "toml": r"+++",
    "yaml": r"---",
}

_LOADERS = {
    "toml": toml.loads,
    "yaml": yaml.safe_load,
}


@parameters(
    jsonschema={
        "type": "object",
        "properties": {
            "delimiter": {"type": "string"},
            "format": {"type": "string", "enum": ["yaml", "toml"]},
            "overwrite": {"type": "boolean"},
        },
    }
)
def process(app, stream, *, format="yaml", delimiter=None, overwrite=True):
    loader = _LOADERS[format]
    delimiter = re.escape(delimiter or _DELIMITERS[format])
    re_frontmatter = re.compile(
        rf"""
        ^{delimiter}\n
         (?P<frontmatter>.*)\n
         {delimiter}\n
         (?P<content>.*)
        """,
        re.DOTALL | re.VERBOSE,
    )

    for item in stream:
        if match := re_frontmatter.match(item["content"]):
            item["content"] = match.group("content")
            frontmatter = loader(match.group("frontmatter"))

            if not isinstance(frontmatter, collections.abc.Mapping):
                raise ValueError(
                    "Frontmatter must be a mapping (i.e. key-value pairs), "
                    "not arrays."
                )

            for key, value in frontmatter.items():
                if overwrite or key not in item:
                    item[key] = value
        yield item
