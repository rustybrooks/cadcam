#!/usr/bin/env python

if __name__ == '__main__':
    import optparse
    import os, sys
    from Tkinter import *

    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    basedir = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(os.path.abspath(os.path.join(basedir, '..')))

    print sys.path

    import utils, menus, wizards

    class App(Tk):
        def __init__(self, options):
            Tk.__init__(self)
            self.options = options
            self.title("CAM Machiner")

            # but this works too
            Tk.report_callback_exception = utils.show_error

            w = wizards.Wizards(top=self)
            win = {}
            win['menu'] = menus.setup_menu(self)

    if __name__ == '__main__':
        parser = optparse.OptionParser()
        options, args = parser.parse_args()

        app = App(options)
        app.mainloop()
