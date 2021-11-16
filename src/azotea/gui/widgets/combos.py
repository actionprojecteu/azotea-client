# ----------------------------------------------------------------------
# Copyright (c) 2021
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import tkinter as tk
import tkinter.ttk as ttk

#--------------
# local imports
# -------------

from azotea.utils import chop
from azotea.utils.roi import Rect

class DimensionCombo(tk.Frame):

    def __init__(self, parent, command=None, text='', tip=None,**kwargs):
        super().__init__(parent)
        label = ttk.Label(self, text=text)
        label.pack(side=tk.TOP,  expand=True, fill=tk.X, padx=5, pady=2)
        combo = ttk.Combobox(self, state='readonly', values=tuple(), **kwargs)
        combo.pack(side=tk.TOP, fill=tk.X, expand=True,  padx=5, pady=0)
        combo.bind('<<ComboboxSelected>>', self._onComboSelection)
        self._combo = combo
        self._command = command
        if tip:
            ToolTip(self._combo, tip)

    def configure(self, **kwargs):
        if state in kwargs and (kargs['state'] == 'normal' or kargs['state'] == 'enabled'):
            kargs['state'] = 'readonly'
        self._combo.configure(**kwargs)


    def get(self):
        return self.fromDisplay(self._combo.get())

    def set(self, value):
        new_item = self.toDisplay(value)
        items = sorted(list(set(self._combo['values']).union(set([new_item]))))
        index = items.index(new_item)
        self._combo['values'] = items
        self._combo.set(new_item)
        self._combo.current(index)

    def clear(self):
         self._combo['values'] = tuple()

    def fill(self, values):
        self._combo['values'] = tuple(self.toDisplay(item) for item in values)

    def _onComboSelection(self, event):
        data = self.fromDisplay(self._combo.get())
        if self._command:
            self._command(data)      
       
    def toDisplay(self, item):
        '''Single item as a dictionary to string display format in combo box'''
        raise NotImplementedError
    

    def fromDisplay(self, item):
        '''From string display format in combo box as a dictionary'''
        raise NotImplementedError



class LocationCombo(DimensionCombo):

    def toDisplay(self, item):
        return ' - '.join([item['site_name'], item['location']])

    def fromDisplay(self, label):
        return dict(zip(('site_name', 'location'), chop(label, sep=' - ')))


class ObserverCombo(DimensionCombo):

    def toDisplay(self, item):
        return ', '.join([item['surname'], item['family_name']])

    def fromDisplay(self, label):
        return dict(zip(('surname', 'family_name'), chop(label, sep=',')))

    
class CameraCombo(DimensionCombo):

    def toDisplay(self, item):
        return item['model']

    def fromDisplay(self, label):
        return dict(zip(('model',), (label.strip(),)))


class ROICombo(DimensionCombo):
    
    def toDisplay(self, item):
        return  str(Rect.from_dict(item))

    def fromDisplay(self, label):
        if label == '':
            result = {}
        else:
            result = Rect.from_string(label).to_dict()
            result['display_name'] = label
        return result
