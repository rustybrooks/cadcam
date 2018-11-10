#!/usr/bin/python

from Tkinter import Tk, Frame, Label, Button, Text, Scrollbar, Checkbutton
from Tkinter import BOTH, LEFT, RIGHT, TOP, BOTTOM, X, Y

import os
import subprocess
import sys

if sys.platform == "win32":
    import msvcrt
    import _subprocess
else:
    import fcntl

class GCodeBrowser(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent

        button_frame = Frame(self)
        button_frame.pack(side=TOP, fill=X, expand=0)
        text_frame = Frame(self)
        text_frame.pack(side=TOP, fill=BOTH, expand=1)

        t = Text(text_frame)
        t.pack(side=LEFT, fill=BOTH, expand=1)
        s = Scrollbar(text_frame)
        s.pack(side=LEFT, fill=Y, expand=1)

        bplay = Button(button_frame, text='Play', command=self.foo)
        bnext = Button(button_frame, text='Next')
        cplot = Checkbutton(button_frame, text="Backplot")
        cmat = Checkbutton(button_frame, text="Material")
        cbit = Checkbutton(button_frame, text="Bit")
        cpause1 = Checkbutton(button_frame, text="Pause after line")
        cpause2 = Checkbutton(button_frame, text="Pause after cmt")

        bplay.pack(side=LEFT)
        bnext.pack(side=LEFT)
        cplot.pack(side=LEFT)
        cmat.pack(side=LEFT)
        cbit.pack(side=LEFT)
        cpause1.pack(side=LEFT)
        cpause2.pack(side=LEFT)

    def foo(self):
        print "About to write to", pipeout
        #cmdout.write("This is a foo\n")
        os.write(pipein, "This is a foo\n")
        #os.close(pipeout)

class Interface(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent, background="white")

        self.parent = parent
        self.parent.title("campy")
        self.pack(fill=BOTH, side=TOP, expand=1)

        gc = GCodeBrowser(self)
        gc.pack(side=LEFT, fill=Y, expand=0)

def setup_pipes():
    global pipearg, pipein

    pipeout, pipein = os.pipe()

    # Prepare to pass to child process
    if sys.platform == "win32":
        curproc = _subprocess.GetCurrentProcess()
        pipeouth = msvcrt.get_osfhandle(pipeout)
        pipeoutih = _subprocess.DuplicateHandle(curproc, pipeouth, curproc, 0, 1, _subprocess.DUPLICATE_SAME_ACCESS)

        pipearg = str(int(pipeoutih))
    else:
        pipearg = str(pipeout)

        # Must close pipe input if child will block waiting for end
        # Can also be closed in a preexec_fn passed to subprocess.Popen
        fcntl.fcntl(pipein, fcntl.F_SETFD, fcntl.FD_CLOEXEC)

def main():
    #global pipearg, pipein
    setup_pipes()

    ourpath = os.path.split(os.path.realpath(__file__))[0]

    exe = os.path.join(ourpath, 'sim', 'sim')
    cwd = os.path.join(ourpath, 'sim')
    cmd = [exe, '--pipein', pipearg]
    print "cmd", cmd, cwd
    subprocess.Popen(cmd,
        close_fds=False,
        cwd=cwd,
        preexec_fn=None if sys.platform == "win32" else lambda: os.close(pipein)
    )

    #cmdout = os.fdopen(pipeout)

    root = Tk()
    root.geometry("700x900")
    app = Interface(root)
    root.mainloop()


if __name__ == '__main__':
    main()
