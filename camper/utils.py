
from Tkinter import *
import traceback


def show_error(self, *args, **kwargs):
    top = Toplevel()
    top.wm_title = "An error occurrend"

    if 'message' in kwargs:
        err = [kwargs['message']]
    else:
        err = traceback.format_exception(*args)

    f1 = Frame(top)
    f2 = Frame(top)
    f1.pack(side=TOP, fill=BOTH, expand=True)
    f2.pack(side=TOP, fill=X, expand=False)

    t = Text(f1, width=120)
    s = Scrollbar(f1)
    t.pack(side=LEFT, fill=BOTH, expand=1)
    s.pack(side=LEFT, fill=Y, expand=0)

    t.config(yscrollcommand=s.set)
    s.config(command=t.yview)

    t.insert(END, '\n'.join([x.rstrip() for x in err]))
    t.configure(state=DISABLED)

    b = Button(f2, text="OK", command=top.destroy)
    b.pack(side=LEFT, fill=BOTH, expand=1)

    top.bind_all("<Key-Escape>", lambda *x, **y: top.destroy)
    t.bind_all("<Key-Escape>", lambda *x, **y: top.destroy)
