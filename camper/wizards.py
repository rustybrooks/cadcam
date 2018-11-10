from Tkinter import *
import ttk

import campy


class Wizard(object):
    def __init__(self, root, wizard_type, wizard):
        self.root = root
        self.wizard_type = wizard_type
        self.wizard = wizard


class FaceWizard(Wizard):
    def __init__(self, root, wizard_type, wizard):
        super(FaceWizard, self).__init__(root, wizard_type, wizard)


class Wizards(object):
    @classmethod
    def memorialize(cls, fn, *args, **kwargs):
        print "memorialize", fn, args, kwargs
        return lambda x: fn(*args, **kwargs)

    def __init__(self, top):
        self.top = top

        pw = ttk.PanedWindow(self.top, orient=HORIZONTAL)
        pw.pack(side=TOP, fill=BOTH, expand=True)

        tree = ttk.Treeview(pw, selectmode='browse', show='tree')
        pw2 = PanedWindow(pw, orient=VERTICAL)

        pw.add(tree)
        pw.add(pw2)

        self.topframe = Frame()
        self.canvas = Canvas(bg='blue')

        self.buttonbar = Frame(self.topframe)
        self.wizardframe = Frame(self.topframe)
        self.buttonbar.pack(side=TOP, fill=X, expand=0)
        self.wizardframe.pack(side=TOP, fill=BOTH, expand=1)

        Button(self.buttonbar, text="Material").pack(side=LEFT, expand=0, fill=None)
        Button(self.buttonbar, text="Tool").pack(side=LEFT, expand=0, fill=None)

        # self.text = Text(pw2, state=DISABLED, bg='blue')

        pw2.add(self.topframe)
        pw2.add(self.canvas)

        self.wizards = {
            'facing': [
                {'label': 'HSM Endmill', 'key': 'facing-endmill-hsm'},
            ],
            'pocketing': [
                {'label': 'HSM Rectangular', 'key': 'pocketing-rect-hsm'},
                {'label': 'HSM Circular', 'key': 'pocketing-circ-hsm'},
            ],
            'drilling': [

            ],
            'grooving': [
                {'label': 'HSM Straight Groove', 'key': 'grooving-straight-hsm'},
            ],
        }

        labels = {
            'facing': 'Facing',
            'pocketing': 'Pocketing',
            'drilling': 'Drill',
        }

        for wt in ['facing', 'pocketing']:
            tree.insert('', END, text=labels[wt], iid=wt)
            for w in self.wizards[wt]:
                tree.insert(wt, END, text=w['label'], iid=w['key'], tags=w['key'])
                tree.tag_bind(w['key'], '<Button-1>', callback=self.memorialize(
                    self.wizard_callback, wt, w
                ))

    def wizard_callback(self, wizard_type, wizard):
        print wizard_type, wizard