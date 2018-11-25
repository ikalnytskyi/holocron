"""Parse YAML front matter and set its values as document attributes."""

import re

import yaml
import schema

from ._misc import iterdocuments, parameters


@parameters(
    schema={
        'when': schema.Or([{str: object}], None, error='unsupported value'),
        'delimiter': schema.Schema(str),
        'overwrite': schema.Schema(bool),
    }
)
def process(app, documents, when=None, delimiter='---', overwrite=True):
    delimiter = re.escape(delimiter)

    for document in iterdocuments(documents, when):
        match = re.match(
            # Match block between delimiters and block outsides of them, if
            # the block between delimiters is on the beginning of content.
            r'{0}\s*\n(.*)\n{0}\s*\n(.*)'.format(delimiter),
            document['content'], re.M | re.S)

        if match:
            headers, document['content'] = match.groups()

            for key, value in yaml.safe_load(headers).items():
                if overwrite or key not in document:
                    document[key] = value

    return documents
