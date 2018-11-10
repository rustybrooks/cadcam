from Tkinter import *
# from ttk import *


def safe_exit():
    print "Exiting..."
    sys.exit(0)


def toplevel_command(title, winclass):
    print "top..."
    t = Toplevel()
    t.title(title)
    w = winclass(top=t)
    return w


def setup_menu(root):
    global win

    menubar = Menu(root, tearoff=False)

    menuspec = {
        'File': [
            ('Exit', ['command', {'label': 'Exit..', 'shortcut': 'Command+x', 'command': lambda *x: safe_exit()}])
        ],
    }

    build_menus(root, menubar, menuspec, keys=['File'])

    root.config(menu=menubar)
    return menubar


def build_menus(root, menubar, menuspec, keys):
    for key in keys:
        spec_list = menuspec[key]
        menubar.add_cascade(label=key, menu=build_cascade(root, menubar, spec_list))


def build_cascade(root, menubar, spec_list):
    button = Menu(menubar, tearoff=False)

    for cmdlist in spec_list:
        label, spec = cmdlist
        stype, data = spec
        if stype == "command":
            button.add_command(
                label=data['label'],
                command=data['command'],
                underline=data.get('underline'),
                accelerator=data.get('shortcut')
            )
        if data.get('shortcut'):
            shortcut = '<{}>'.format(data['shortcut'].replace('+', '-'))
            print "Binding", shortcut
            root.bind_all(shortcut, data['command'])

    return button