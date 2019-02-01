"""Strip .HTML extension from URIs."""

import os


def process(app, stream):
    for item in stream:
        destination = os.path.basename(item["destination"])

        # Most modern HTTP servers implicitly serve one of these files when
        # requested URL is pointing to a directory on filesystem. Hence in
        # order to provide "pretty" URLs we need to transform destination
        # address accordingly.
        if destination not in ("index.html", "index.htm"):
            item["destination"] = os.path.join(
                os.path.splitext(item["destination"])[0], "index.html")

        yield item
