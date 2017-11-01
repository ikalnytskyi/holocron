"""Run separate processors pipeline on selected documents."""


from ._misc import iterdocuments_ex


def process(app, documents, **options):
    processors = options.pop('processors', [])
    when = options.pop('when', None)

    kept = []
    selected = []

    for document, is_matched in iterdocuments_ex(documents, when):
        if is_matched:
            selected.append(document)
        else:
            kept.append(document)

    return kept + app.invoke_processors(selected, processors)
