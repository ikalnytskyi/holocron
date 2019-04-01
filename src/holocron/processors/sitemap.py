"""Generate Sitemap XML."""

import os
import itertools
import gzip as _gzip
import xml.dom.minidom as minidom

from ..core import WebSiteItem
from ._misc import parameters


@parameters(
    jsonschema={
        "type": "object",
        "properties": {
            "gzip": {"type": "boolean"},
            "save_as": {"type": "string"},
            "pretty": {"type": "boolean"},
        },
    }
)
def process(app, stream, *, gzip=False, save_as="sitemap.xml", pretty=True):
    passthrough, stream = itertools.tee(stream)

    sitemap = WebSiteItem(
        {
            "source": "sitemap://%s" % save_as,
            "destination": save_as,
            "baseurl": app.metadata["url"],
        }
    )
    sitemap["content"] = _create_sitemap_xml(stream, sitemap, pretty)

    # According to the Sitemap protocol, the sitemap.xml can be compressed
    # using gzip to reduce bandwidth requirements. While HTTP can does
    # compression on fly for us, doing so requires CPU work on the server as
    # well as proper configuration of web server software.
    if gzip:
        sitemap["content"] = _gzip.compress(sitemap["content"])
        sitemap["source"] += ".gz"
        sitemap["destination"] += ".gz"

    yield from passthrough
    yield sitemap


def _create_sitemap_xml(stream, sitemap, pretty):
    dom = minidom.Document()
    urlset = dom.createElement("urlset")
    urlset.setAttribute("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    dom.appendChild(urlset)

    # Everything under the same directory is owned by a sitemap, and thus can
    # be enlisted in the sitemap.
    owned_url = os.path.dirname(sitemap["absurl"]) + "/"

    for item in stream:
        if not item["absurl"].startswith(owned_url):
            raise ValueError(
                "The location of a Sitemap file determines the set of URLs "
                "that can be included in that Sitemap. A Sitemap file located "
                "at %s can include any URLs starting with %s but can not "
                "include %s." % (sitemap["absurl"], owned_url, item["absurl"])
            )

        url = dom.createElement("url")
        loc = dom.createElement("loc")
        loc.appendChild(dom.createTextNode(item["absurl"]))
        url.appendChild(loc)
        lastmod = dom.createElement("lastmod")
        lastmod.appendChild(dom.createTextNode(item["updated"].isoformat()))
        url.appendChild(lastmod)
        urlset.appendChild(url)

    # According to the sitemap protocol, the encoding must always be UTF-8.
    # That's why sitemap processor supports no encoding parametrization.
    if pretty:
        sitemap_xml = dom.toprettyxml(indent="  ", encoding="UTF-8")
    else:
        sitemap_xml = dom.toxml(encoding="UTF-8")
    return sitemap_xml
