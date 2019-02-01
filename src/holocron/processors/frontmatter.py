"""Parse YAML front matter and set its values as item"s properties."""

import re

import yaml
import schema

from ._misc import parameters


@parameters(
    schema={
        "delimiter": schema.Schema(str),
        "overwrite": schema.Schema(bool),
    }
)
def process(app, stream, *, delimiter="---", overwrite=True):
    delimiter = re.escape(delimiter)

    for item in stream:
        match = re.match(
            # Match block between delimiters and block outsides of them, if
            # the block between delimiters is on the beginning of content.
            r"{0}\s*\n(.*)\n{0}\s*\n(.*)".format(delimiter),
            item["content"], re.M | re.S)

        if match:
            headers, item["content"] = match.groups()

            for key, value in yaml.safe_load(headers).items():
                if overwrite or key not in item:
                    item[key] = value

        yield item
