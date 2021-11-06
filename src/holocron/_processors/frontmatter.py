"""Parse YAML front matter and set its values as item"s properties."""

import collections.abc
import json
import re

from ._misc import parameters


class _FrontmatterParser:
    """Parse frontmatter using one of the supported formats."""

    def __init__(self, format):
        self._parsers = {"json": json.loads}
        self._try_next_exceptions = [json.JSONDecodeError]
        self._format = format

        try:
            import toml
        except ImportError:
            pass
        else:
            self._parsers["toml"] = toml.loads
            self._try_next_exceptions.append(toml.TomlDecodeError)

        try:
            import yaml
        except ImportError:
            pass
        else:
            # YAML is too eager and can parse TOML as plain YAML string. Since
            # frontmatter must be a mapping, it's not what a user would expect.
            # In order to prevent such issues, we must ensure that YAML parser
            # goes last.
            self._parsers["yaml"] = yaml.safe_load
            self._try_next_exceptions.append(yaml.YAMLError)

        # If a user passed the format of frontmatter, we can save some CPU
        # cycles and avoid parsing using other available parsers. Moreover,
        # specifying the format explicitly may result into returning better
        # error.
        if self._format:
            self._parsers = {self._format: self._parsers[self._format]}

    def __call__(self, frontmatter):
        for _, parse in self._parsers.items():
            try:
                rv = parse(frontmatter)
            except tuple(self._try_next_exceptions):
                # If there's only one parser to try, we can propagate its
                # exception up above in order to provide more context
                # regarding the error.
                if self._format:
                    raise
                continue

            if not isinstance(rv, collections.abc.Mapping):
                raise ValueError(
                    "Frontmatter must be a mapping (i.e. key-value pairs), "
                    "not arrays."
                )
            return rv

        raise ValueError(
            f"Frontmatter cannot be parsed as one of the supported formats: "
            f"{', '.join(self._parsers)}"
        )


@parameters(
    jsonschema={
        "type": "object",
        "properties": {
            "delimiter": {"type": "string"},
            "overwrite": {"type": "boolean"},
            "format": {"type": "string", "enum": ["yaml", "json", "toml"]},
        },
    }
)
def process(app, stream, *, delimiter="---", overwrite=True, format=None):
    r"""Parse documents' front matter blocks and assign properties on them.

    The front matter must be the first thing in the file and must take the form
    of JSON, TOML or YAML set between triple-dashed line (``---``). Between
    these triple-dashed lines, you can set various variables that will then be
    set as properties on corresponding document items.

    Assuming you have the following input document

    .. code:: json

       {
          "content": "---\\nauthor: Batman\\n---\\n\\nI'm Batman!\\n"
       }

    the front matter processor will transform it into the following one:

    .. code:: json

       {
          "author": "Batman",
          "content": "I'm Batman!\\n"
       }

    Parameters
    ``````````

    :delimiter:
        The delimiter to separate document's content from the front matter
        block. ``---`` is used by default.

    :overwrite:
        When ``true``, the metadata from the front matter block is assigned on
        the document from the stream even if it's already set.

    :format:
        The format of front matter blocks to parse in your documents. Could be
        ``json``, ``toml`` or ``yaml``. If not specified, the formats are
        probed one by one in the mentioned order.

    Example
    ```````

    .. code:: yaml

       - name: frontmatter
         args:
           delimiter: +++
           format: toml
    """

    delimiter = re.escape(delimiter)
    parser = _FrontmatterParser(format)

    for item in stream:
        match = re.match(
            # Match block between delimiters and block outsides of them, if
            # the block between delimiters is on the beginning of content.
            rf"\s*{delimiter}\s*\n(.*)\n{delimiter}\s*\n(.*)",
            item["content"],
            re.M | re.S,
        )

        if match:
            frontmatter, item["content"] = match.groups()

            for key, value in parser(frontmatter).items():
                if overwrite or key not in item:
                    item[key] = value

        yield item
