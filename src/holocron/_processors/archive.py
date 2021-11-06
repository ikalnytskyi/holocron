"""Generate an archive page."""

import itertools
import pathlib

import holocron

from ._misc import parameters


@parameters(
    jsonschema={
        "type": "object",
        "properties": {
            "template": {"type": "string"},
            "save_as": {"type": "string"},
        },
    }
)
def process(app, stream, *, template="archive.j2", save_as="index.html"):
    """Generate an archive page for a given stream.

    Parameters
    ``````````

    :template: an HTML template to use to produce a new archive page
    :save_as: desired destination of a produced archive page

    Example
    ```````

    .. code:: yaml

       - name: archive
         args:
           template: index.j2
    """

    passthrough, stream = itertools.tee(stream)
    index = holocron.WebSiteItem(
        {
            "source": pathlib.Path("archive://", save_as),
            "destination": pathlib.Path(save_as),
            "template": template,
            "items": list(stream),
            "baseurl": app.metadata["url"],
        }
    )

    yield from passthrough
    yield index
