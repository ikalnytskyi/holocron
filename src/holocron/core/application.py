"""Holocron, The Application."""

import collections

from ..processors import _misc


class Application:
    """Application instance orchestrates processors execution."""

    def __init__(self, metadata=None):
        # Metadata is a KV store shared between processors. It serves two
        # purposes: first, metadata contains an application level data, and
        # secondly, it's the only way to consume artifacts produced by one
        # processor from another processor.
        #
        # ChainMap is used to prevent writes to original metadata mapping,
        # and thus making it easier to distinguish initial metadata values
        # from the one set by processors in the mid of troubleshooting.
        self._metadata = collections.ChainMap({}, metadata or {})

        # Processors are (normally) stateless functions that receive an input
        # stream of items and produce an output stream of items. This property
        # keeps track of known processors, and is used to retrieve processors
        # one someone asked to execute a pipe.
        self._processors = {}

        # Pipes are sets of processors connected in series, where the output
        # of one processor is the input of the next one. This property keeps
        # track of known pipes, and is used to execute processors in sequence
        # when invoked.
        self._pipes = {}

    @property
    def metadata(self):
        return self._metadata

    def add_processor(self, name, processor):
        self._processors[name] = processor

    def add_pipe(self, name, pipe):
        self._pipes[name] = pipe

    def invoke(self, pipe, stream=None):
        # A given 'pipe' may be either a pipe name or an actual
        # pipe definition. That's why need this ugly type check because any
        # string value is considered as a name. Passing an actual pipe is
        # very handy in couple of use cases, such as running a sub pipe
        # from some processor.
        if isinstance(pipe, str):
            if pipe not in self._pipes:
                raise ValueError("no such pipe: '%s'" % pipe)
            pipe = self._pipes[pipe]

        # Since processors expect an input stream to be an iterator, we cast a
        # given stream explicitly to an iterator even though everything will
        # probably work even if it's not. We just want to respect and enforce
        # established contracts.
        stream = iter(stream or [])

        for processor in pipe:
            processor = processor.copy()
            processor_name = processor.pop("name")

            if processor_name not in self._processors:
                raise ValueError("no such processor: '%s'" % processor_name)

            processfn = self._processors[processor_name]

            # Resolve every JSON reference we encounter in a processor's
            # parameters. Please note, we're doing this so late because we
            # want to take into account metadata and other changes produced
            # by previous processors in the pipe.
            processor = _misc.resolve_json_references(
                processor, {"metadata:": self.metadata})

            stream = processfn(self, stream, **processor)

        yield from stream
