def frange(start, stop, step, include_end=True):
    if start < stop:
        while start < stop:
            yield start
            start += step
    else:
        while start > stop:
            yield start
            start -= step

    if include_end and start <= stop:
        yield stop
