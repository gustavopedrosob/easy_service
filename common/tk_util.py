import locale
import re
from tkinter import Spinbox as _Spinbox, StringVar, Menu
from tkinter import Entry as _Entry
from tkinter.ttk import Treeview as _Treeview
from typing import Optional

from pyperclip import paste


locale.setlocale(locale.LC_MONETARY, 'pt_BR.UTF-8')


class Treeview(_Treeview):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.popup = Menu(self, tearoff=False)
        self.unbind_class("Treeview", "<Button-1>")
        self.bind("<Button-1>", self.__on_click)
        self.bind("<Button-3>", self.__do_popup)
        self.bind("<Motion>", "break")

    def __do_popup(self, event):
        try:
            selected = self.selection()[0]
        except IndexError:
            pass
        else:
            _, selected_y, _, selected_height = self.bbox(selected)
            if selected_y < event.y < selected_y + selected_height:
                self.popup.post(event.x_root, event.y_root)

    def __on_click(self, event):
        self.focus_set()
        try:
            selected = self.selection()[0]
        except IndexError:
            selected = None
        row_clicked = self.identify_row(event.y)
        if selected:
            if selected == row_clicked:
                self.selection_remove(row_clicked)
            else:
                self.selection_set(row_clicked)
        else:
            self.selection_set(row_clicked)


class _EasyControlV:
    @staticmethod
    def _on_control_v(event):
        control_v_content = paste()
        control_v_content = control_v_content.strip()
        event.widget.insert(0, control_v_content)


class Spinbox(_Spinbox, _EasyControlV):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unbind_class("Spinbox", "<Control-v>")
        self.bind("<Control-v>", self._on_control_v)


class Entry(_Entry, _EasyControlV):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unbind_class("Entry", "<Control-v>")
        self.bind("<Control-v>", self._on_control_v)


class StrVar(StringVar):
    def reset(self):
        self.set("")

    def is_empty(self):
        return self.get() == ""


class IntStr(StrVar):
    def is_valid(self, max_: Optional[int] = None, min_: Optional[int] = None):
        return self.is_text_valid(self.get(), max_, min_)

    @staticmethod
    def is_text_valid(string: str, max_: Optional[int] = None, min_: Optional[int] = None):
        if string:
            try:
                integer = int(string)
            except ValueError:
                return False
            else:
                is_min, is_max = True, True
                if min_:
                    if integer < min_:
                        is_min = False
                if max_:
                    if integer > max_:
                        is_max = False
                return is_min and is_max
        else:
            return True


class BRLVar(StrVar):
    def is_valid_for_input(self):
        return self.is_text_valid_for_input(self.get())

    @staticmethod
    def is_text_valid_for_input(text: str):
        if text:
            compiled = re.compile(
                r"^(([1-9]\d{2}|[1-9]\d|[1-9])\.?\d{0,3}((?<=\d{3})(,\d{0,2}))?|([1-9]\d{2}|[1-9]\d|\d)(,\d{0,2})?)$")
            return bool(compiled.match(text))
        else:
            return True

    def is_valid(self) -> bool:
        compiled = re.compile(r"^(([1-9]\d{2}|[1-9]\d|[1-9])\.?\d{3}|([1-9]\d{2}|[1-9]\d|\d))(,\d{1,2})?$")
        return bool(compiled.match(self.get()))

    def get_formated(self) -> str:
        return locale.currency(self.to_float(), grouping=True)

    def to_float(self):
        return float(self.get().replace(".", "").replace(",", "."))

    def copy(self):
        return BRLVar(value=self.get())

    def validate(self):
        if self.is_empty():
            raise ValueError("Entrada de valor em reais não preenchida.")
        if not self.is_valid():
            raise ValueError("Entrada de valor em reais inválida.")
