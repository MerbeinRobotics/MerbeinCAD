"""Accessible mouse hover tooltips for tkinter and ttk buttons."""
import tkinter as tk


class ToolTip:
    def __init__(self, widget, text, delay_ms=500):
        self.widget, self.text, self.delay_ms = widget, text, delay_ms
        self.job = None
        self.popup = None
        widget.bind('<Enter>', self.queue, add='+')
        widget.bind('<Leave>', self.hide, add='+')
        widget.bind('<ButtonPress>', self.hide, add='+')
        widget.bind('<Destroy>', self.hide, add='+')

    def queue(self, event=None):
        self.hide()
        self.job = self.widget.after(self.delay_ms, self.show)

    def show(self):
        self.job = None
        if not self.widget.winfo_exists():return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.popup = tk.Toplevel(self.widget)
        self.popup.wm_overrideredirect(True)
        try:self.popup.wm_attributes('-topmost', True)
        except tk.TclError:pass
        frame = tk.Frame(self.popup, bg='#fff8d5', bd=1, relief='solid')
        frame.pack()
        tk.Label(frame, text=self.text, bg='#fff8d5', fg='#172232',
                 font=('Segoe UI', 10), padx=8, pady=5).pack()
        self.popup.wm_geometry(f'+{x}+{y}')

    def hide(self, event=None):
        if self.job is not None:
            try:self.widget.after_cancel(self.job)
            except tk.TclError:pass
            self.job = None
        if self.popup is not None:
            try:self.popup.destroy()
            except tk.TclError:pass
            self.popup = None
