from . import operation, machine


@operation(required=['center', 'z', 'depth'], operation_feedrate='probe')
def zprobe(
    center=None, z=None, depth=None, rate=None, toward=True, halt_on_error=True,
    tries=1, backoff=.5
):
    x, y = center
    machine().goto(z=z)
    machine().goto(x, y)

    for i in range(tries):
        machine().probe(axis='Z', to=z-depth, rate=rate*(backoff**i), toward=toward, halt_on_error=halt_on_error)
        machine().probe(axis='Z', to=z, rate=rate, toward=not toward, halt_on_error=halt_on_error)