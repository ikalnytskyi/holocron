"""Inspect Holocron sources and inject documentation."""

import inspect
import re


class _MarkupInjector:
    """Replace <!-- inject: something --> with content."""

    _re_injections_format = r"..\s+inject:\s+%s\s+"
    _re_injections = {
        "processors-docs": "processors_docs",
    }

    def __init__(self, processors):
        self._processors = processors
        self._re_injections = {
            re.compile(self._re_injections_format % point): getattr(self, property_)
            for point, property_ in self._re_injections.items()
        }

    def process(self, content):
        for regex, injection in self._re_injections.items():
            content = regex.sub(injection, content)
        return content

    @property
    def processors_docs(self):
        processors_docs = []

        for name, processor in self._processors.items():
            anchor = f".. _{name}:"
            ref_name = f"`{name}`_"

            processor_docs = [
                anchor,
                "",
                ref_name,
                "-" * len(ref_name),
                "",
                inspect.getdoc(processor) or "",
            ]
            processors_docs.append("\n".join(processor_docs))

        return "\n\n".join(processors_docs)


def process(app, stream, *, exceptions=None):
    injector = _MarkupInjector(
        {
            name: processor
            for name, processor in app._processors.items()
            if processor.__module__.startswith("holocron")
        }
    )

    for item in stream:
        item["content"] = injector.process(item["content"])
        yield item
