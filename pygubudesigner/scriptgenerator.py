# encoding: utf-8
import os
import sys
import logging

try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog
    from tkinter import messagebox
except:
    import Tkinter as tk
    import ttk
    import tkMessageBox as messagebox
    import tkFileDialog as filedialog
import pygubu
from .codebuilder import UI2Code

logger = logging.getLogger(__name__)
FILE_PATH = os.path.dirname(os.path.abspath(__file__))


TPL_APPLICATION = \
"""import os
import pygubu


PROJECT_PATH = os.path.dirname(__file__)
PROJECT_UI = os.path.join(PROJECT_PATH, "{project_name}")


class {class_name}:
    def __init__(self):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object('{main_widget}')
        builder.connect_callbacks(self)
    
{callbacks}
    def run(self):
        self.mainwindow.mainloop()


if __name__ == '__main__':
    app = {class_name}()
    app.run()

"""

TPL_CODESCRIPT = \
"""{import_lines}


class {class_name}:
    def __init__(self, master=None):
        # build ui
{widget_code}
        # Main widget
        self.mainwindow = {main_widget}

{callbacks}
    def run(self):
        self.mainwindow.mainloop()


if __name__ == '__main__':
    app = {class_name}()
    app.run()
"""

TPL_WIDGET = \
"""{import_lines}


class {class_name}({widget_base_class}):
    def __init__(self, master=None, **kw):
        {widget_base_class}.__init__(self, master, **kw)
{widget_code}
{callbacks}

if __name__ == '__main__':
    root = tk.Tk()
    widget = {class_name}(root)
    widget.pack(expand=True, fill='both')
    root.mainloop()

"""


class ScriptGenerator(object):
    def __init__(self, app):
        self.app = app
        self.builder = builder = app.builder
        self.tree = app.tree_editor
        self.projectname = ''

        self.widgetlist = builder.get_object('widgetlist')
        self.widgetlistvar = builder.get_variable('widgetlistvar')
        self.widgetlist_keyvar = builder.get_variable('widgetlist_keyvar')
        
        #self.templatelist = builder.get_object('templatelist')
        #self.templatelistvar = builder.get_variable('templatelistvar')
        self.template_var = builder.get_variable('template_var')
        
        self.classnamevar = builder.get_variable('classnamevar')
        self.txt_code = builder.get_object('txt_code')
        
        self.template_desc_var = builder.get_variable('template_desc_var')
        
        _ = self.app.translator
        self.template_desc = {
            'application': _('Create a pygubu application script using the UI definition.'),
            'codescript': _('Create a coded version of the UI definition.'),
            'widget': _('Create a base class for your custom widget.')
        }
        
    def camel_case(self, st):
        output = ''.join(x for x in st.title() if x.isalnum())
        return output
    
    def on_code_generate_clicked(self):
        if self.form_valid():
            tree_item = self.widgetlist_keyvar.get()
            params = {
                'project_name': self.projectname,
                'class_name': self.classnamevar.get(),
                'main_widget': self.tree.get_widget_id(tree_item),
                'widget_base_class': self.tree.get_widget_class(tree_item),
                'widget_code': None,
                'import_lines': None,
                'callbacks': ''
            }
            template = self.template_var.get()
            if template == 'application':
                code = TPL_APPLICATION.format(**params)
                self.set_code(code)
            elif template == 'widget':
                generator = UI2Code()
                uidef = self.tree.tree_to_uidef()
                target = self.tree.get_widget_id(tree_item)
                code = generator.generate(uidef, target)
                params['widget_code'] = code[target]
                params['import_lines'] = code['imports']
                params['callbacks'] = code['callbacks']
                code = TPL_WIDGET.format(**params)
                self.set_code(code)
            elif template == 'codescript':
                generator = UI2Code()
                uidef = self.tree.tree_to_uidef()
                target = self.tree.get_widget_id(tree_item)
                code = generator.generate(uidef, target, as_class=False, tabspaces=8)
                params['widget_code'] = code[target]
                params['import_lines'] = code['imports']
                params['callbacks'] = code['callbacks']
                code = TPL_CODESCRIPT.format(**params)
                self.set_code(code)
    
    def on_code_copy_clicked(self):
        pass
    
    def on_code_template_changed(self):
        template = self.template_var.get()
        if template == 'application':
            name = '{0}App'.format(self.get_classname())
            self.classnamevar.set(name)
        elif template == 'codescript':
            pass
        elif template == 'widget':
            name = '{0}Widget'.format(self.get_classname())
            self.classnamevar.set(name)
        # Update template description
        self.template_desc_var.set(self.template_desc[template])
        self.set_code('')
    
    def on_code_save_clicked(self):
        _ = self.app.translator
        filename = (self.classnamevar.get()).lower()
        options = {
            'defaultextension': '.py',
            'filetypes': ((_('Python Script'), '*.py'), (_('All'), '*.*')),
            'initialfile': '{0}.py'.format(filename),
        }
        fname = filedialog.asksaveasfilename(**options)
        if fname:
            with open(fname, 'w') as out:
                out.write(self.get_code())
    
    def configure(self):
        print('configuring...')
        self.projectname = self.app.project_name()
        wlist = self.tree.get_topwidget_list()
        self.widgetlist.configure(values=wlist)
        self.classnamevar.set(self.get_classname())
        
        if len(wlist) > 0:
            key = wlist[0][0]
            self.widgetlist_keyvar.set(key)
        self.template_var.set('application')
        self.set_code(u'')
        
    def get_classname(self):
        name = os.path.splitext(self.projectname)[0]
        return self.camel_case(name)
    
    def form_valid(self):
        valid = True
        
        _ = self.app.translator
        mbtitle = _('Script Generator')
        widget = self.widgetlist.current()
        if widget is None:
            valid = False
            messagebox.showwarning(title=mbtitle, message='Select widget')
        template = self.template_var.get()
        if valid and template is None:
            valid = False
            messagebox.showwarning(title=mbtitle, message='Select template')
        classname = self.classnamevar.get()
        if valid and classname == '':
            valid = False
            messagebox.showwarning(title=mbtitle, message='Enter classname')            
        
        return valid
    
    def set_code(self, text):
        self.txt_code.delete('0.0', 'end')
        self.txt_code.insert('0.0', text)
    
    def get_code(self):
        return self.txt_code.get('0.0', 'end')

