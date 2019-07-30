"""Strip .HTML extension from URIs."""


def process(app, stream):
    for item in stream:
        # Most modern HTTP servers implicitly serve one of these files when
        # requested URL is pointing to a directory on filesystem. Hence in
        # order to provide "pretty" URLs we need to transform destination
        # address accordingly.
        if item["destination"].name not in ("index.html", "index.htm"):
            item["destination"] = item["destination"].parent.joinpath(
                item["destination"].stem, "index.html"
            )

        yield item
