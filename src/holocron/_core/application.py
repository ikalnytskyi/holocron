"""Holocron, The Application."""

import collections
import logging

from .._processors import _misc

_logger = logging.getLogger("holocron")


class Application:
    """Application instance orchestrates processors execution."""

    _processor_reserved_props = frozenset({"name", "args"})

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

        # Processor wrappers are processors that somehow wrap another
        # processor. They receive wrapped processor as input argument and are
        # fully responsible to invoke it when necessary. The only reason why
        # this special type of processors exists in the first place is because
        # Holocron implements syntax sugar for them. Other than that, there is
        # no difference indeed.
        self._processor_wrappers = set()

        # Pipes are sets of processors connected in series, where the output
        # of one processor is the input of the next one. This property keeps
        # track of known pipes, and is used to execute processors in sequence
        # when invoked.
        self._pipes = {}

    @property
    def metadata(self):
        return self._metadata

    def add_processor(self, name, processor):
        if name in self._processors:
            _logger.warning("processor override: '%s'", name)
        self._processors[name] = processor

    def add_processor_wrapper(self, name, processor):
        if name in self._processor_reserved_props:
            raise ValueError(f"illegal wrapper name: {name}")

        self.add_processor(name, processor)
        self._processor_wrappers.add(name)

    def add_pipe(self, name, pipe):
        if name in self._pipes:
            _logger.warning("pipe override: '%s'", name)
        self._pipes[name] = pipe

    def invoke(self, pipe, stream=None):
        # A given 'pipe' may be either a pipe name or an actual
        # pipe definition. That's why need this ugly type check because any
        # string value is considered as a name. Passing an actual pipe is
        # very handy in couple of use cases, such as running a sub pipe
        # from some processor.
        if isinstance(pipe, str):
            if pipe not in self._pipes:
                raise ValueError(f"no such pipe: '{pipe}'")
            pipe = self._pipes[pipe]

        # Since processors expect an input stream to be an iterator, we cast a
        # given stream explicitly to an iterator even though everything will
        # probably work even if it's not. We just want to respect and enforce
        # established contracts.
        stream = iter(stream or [])

        for processor in pipe:
            # Resolve every JSON reference we encounter in a processor's
            # parameters. Please note, we're doing this so late because we
            # want to take into account metadata and other changes produced
            # by previous processors in the pipe.
            processor = _misc.resolve_json_references(
                processor, {"metadata:": self.metadata}
            )

            name, args, kwargs = _unpack_and_wrap_processor(
                processor, self._processor_reserved_props
            )

            if name not in self._processors:
                raise ValueError(f"no such processor: '{name}'")

            processfn = self._processors[name]
            stream = processfn(self, stream, *args, **kwargs)

        yield from stream


def _unpack_and_wrap_processor(processor, processor_reserved_props):
    """Unpack and wrap a given processor.

    Processors may optionally be wrapped in another processors. This can be
    naturally achieved by passing a processor as input to another processor,
    and let the latter to invoke the former. Such syntaxes, however, is
    nested and hence complex. That's why Holocron provides a syntax sugar
    for wrapping processors:

        - name: commonmark
          args:
            ...
          when:
            ...

    where `when` is a wrapping processor and `commonmark` is wrapped
    processor. So this function naturally wraps `commonmark` and so we
    effectively resolve syntax sugar.
    """

    processor_name = processor["name"]
    processor_args = []
    processor_kwrs = {}
    processor_opts = processor.get("args", {})

    wrapper_name = next(
        (k for k in processor if k not in processor_reserved_props), None
    )

    if wrapper_name:
        processor_name = wrapper_name
        processor_args = [processor]
        processor_kwrs = {}
        processor_opts = processor.pop(wrapper_name)

    if isinstance(processor_opts, collections.abc.Sequence):
        processor_args.extend(processor_opts)
    else:
        processor_kwrs.update(processor_opts)

    return processor_name, processor_args, processor_kwrs
