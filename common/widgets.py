import locale
import threading
import tkinter as tk
from tkinter import ttk

import typing

from common import colors, utils

locale.setlocale(locale.LC_MONETARY, 'pt_BR.UTF-8')


def _strip_content(event):
    control_v_content = utils.get_clipboard_content(event.widget)
    control_v_content = control_v_content.strip()
    event.widget.insert(0, control_v_content)


class TreeviewContextMenuManagement:
    def __init__(self, treeview):
        self.treeview = treeview
        self.context_menu_selected = tk.Menu(self.treeview, tearoff=False)
        self.context_menu = tk.Menu(self.treeview, tearoff=False)
        self.treeview.bind("<Button-3>", self.do_popup)

    def do_popup(self, event):
        if self.has_selected():
            self.place_context_menu_selected(event)
        else:
            self.place_context_menu(event)

    def has_selected(self):
        return bool(self.treeview.selection())

    def place_context_menu_selected(self, event):
        selected = self.treeview.selection()[0]
        _, selected_y, _, selected_height = self.treeview.bbox(selected)
        if selected_y < event.y < selected_y + selected_height:
            self.context_menu_selected.post(event.x_root, event.y_root)

    def place_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)


class HoverText:
    def __init__(self, widget, hover_text: typing.Optional[str] = None):
        self.widget = widget
        self.hover_text = hover_text
        toplevel = self.widget.winfo_toplevel()
        self.label = tk.Label(toplevel, highlightthickness=1, highlightbackground=colors.HIGHLIGHT)
        if self.hover_text:
            self.label.config(text=self.hover_text)
        self.place_timer: typing.Optional[threading.Timer] = None
        self.widget.bind("<Enter>", lambda _: self.on_enter())
        self.widget.bind("<Leave>", lambda _: self.on_leave())

    def on_enter(self):
        if self.hover_text:
            self.place_timer = threading.Timer(2, self.routine)
            self.place_timer.start()

    def routine(self):
        toplevel = self.widget.winfo_toplevel()
        coord_x = toplevel.winfo_pointerx() - toplevel.winfo_rootx()
        coord_y = toplevel.winfo_pointery() - toplevel.winfo_rooty() - 32
        self.place_hidden_text(coord_x, coord_y)
        timer = threading.Timer(3, self.hide_hidden_text)
        timer.start()

    def place_hidden_text(self, x: int, y: int):
        self.label.place(x=x, y=y)

    def is_hidden_text_visible(self):
        return self.label.winfo_viewable()

    def hide_hidden_text(self):
        self.label.place_forget()

    def on_leave(self):
        if self.is_hidden_text_visible():
            self.hide_hidden_text()
        if self.place_timer is not None:
            self.place_timer.cancel()
            self.place_timer = None


class Button(tk.Button):
    def __init__(self, master, relief=tk.RIDGE, activebackground=colors.WHITE, hover_text: typing.Optional[str] = None,
                 **kwargs):
        super().__init__(
            master=master,
            relief=relief,
            borderwidth=1,
            activebackground=activebackground,
            **kwargs
        )
        HoverText(self, hover_text)


class Treeview(ttk.Treeview):
    def __init__(self, *args, **kwargs):
        super(Treeview, self).__init__(*args, **kwargs)
        self.bind("<ButtonRelease-1>", self._on_click)
        self.context_menu_management = TreeviewContextMenuManagement(self)
        self._binds = {}
        self.sorting_column = ""
        self.reverse_sorting = False

    def _on_click(self, event):
        region = self.identify_region(event.x, event.y)
        if region == "heading":
            self._on_sorting_click(event)
        elif region == "cell":
            self._on_row_click(event)

    def _on_row_click(self, event):
        selection = self.selection()
        if self.identify_row(event.y) in selection:
            command = self._binds.get("<Select>")
        else:
            command = self._binds.get("<Unselect>")
        if command is not None:
            command(selection)

    def _on_sorting_click(self, event):
        column = self.identify_column(event.x)
        if column == self.sorting_column:
            self.reverse_sorting = not self.reverse_sorting
        else:
            self.reverse_sorting = False
            self.sorting_column = column
        sort_command = self._binds.get("<Sort>")
        if sort_command is not None:
            sort_command(self.sorting_column, self.reverse_sorting)

    def own_bind(self, sequence: str, func) -> None:
        self._binds[sequence] = func


class BrowseTreeview(Treeview):
    def __init__(self, *args, **kwargs):
        super(BrowseTreeview, self).__init__(*args, selectmode="none", **kwargs)

    def _on_row_click(self, event):
        row = self.identify_row(event.y)
        if row in self.selection():
            self.selection_remove(row)
            command = self._binds.get("<Unselect>")
        else:
            self.selection_set(row)
            command = self._binds.get("<Select>")
        if command is not None:
            command(row)


class Placeholder:
    def __init__(self, widget, placeholder, placeholder_color):
        self._widget = widget
        self.__default_config = {
            "foreground": self._widget["foreground"],
            "validate": self._widget["validate"],
            "validatecommand": self._widget["validatecommand"]
        }
        self.__placeholder = placeholder
        self.__placeholder_color = placeholder_color

        self._widget.bind("<FocusIn>", self._on_focus_in)
        self._widget.bind("<FocusOut>", self.on_focus_out)

        self.__placeholder_on()

    def placeholder_config(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__default_config:
                self.__default_config[key] = value
        self._widget.config(**kwargs)

    def __placeholder_on(self):
        self._widget.config(validate="none", validatecommand="", fg=self.__placeholder_color)
        self._widget.delete(0, tk.END)
        self._widget.insert(0, self.__placeholder)

    def __placeholder_off(self):
        self._widget.config(**self.__default_config)

    def _is_using_placeholder_style(self) -> bool:
        return str(self._widget["foreground"]) == self.__placeholder_color

    def _is_using_placeholder_text(self) -> bool:
        return self._widget.get() == self.__placeholder

    def is_using_placeholder(self) -> bool:
        return self._is_using_placeholder_style() and self._is_using_placeholder_text()

    def set_placeholder(self, mode: bool):
        if mode:
            self.__placeholder_on()
        else:
            self.__placeholder_off()

    def __is_empty(self):
        return self._widget.get() == ""

    def _on_focus_in(self, event):
        if self.is_using_placeholder():
            self._widget.delete(0, tk.END)
            self.__placeholder_off()
        # Previne que quando o widget for alterado não continue com o estilo de placeholder.
        # if self._is_using_placeholder_style() and not self._is_using_placeholder_text():
        #     self.__placeholder_off()

    def on_focus_out(self, event):
        if self.__is_empty():
            self.__placeholder_on()

    def set_text(self, text: str):
        self._widget.delete(0, tk.END)
        self.__placeholder_off()
        self._widget.insert(0, text)


class Spinbox(tk.Spinbox, Placeholder):
    def __init__(self, *args, placeholder, width=30, hover_text: typing.Optional[str] = None, placeholder_color="Grey",
                 **kwargs):
        super().__init__(*args, width=width, **kwargs)
        self.unbind_class("Spinbox", "<Control-v>")
        self.bind("<Control-v>", _strip_content)
        HoverText(self, hover_text)
        Placeholder.__init__(self, self, placeholder, placeholder_color)


class Entry(tk.Entry, Placeholder):
    def __init__(self, *args, placeholder, width=30, hover_text: typing.Optional[str] = None,
                 placeholder_color="Grey", **kwargs):
        super().__init__(*args, width=width, **kwargs)
        self.unbind_class("Entry", "<Control-v>")
        self.bind("<Control-v>", _strip_content)
        HoverText(self, hover_text)
        Placeholder.__init__(self, self, placeholder, placeholder_color)


class Combobox(ttk.Combobox):
    def __init__(self, *args, hover_text: typing.Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        HoverText(self, hover_text)
