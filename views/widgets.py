import tkinter as tk


class ToolTip:
    def __init__(
        self,
        widget,
        get_text,
        background="#0f172a",
        foreground="#f8fafc",
    ):
        self.widget = widget
        self.get_text = get_text
        self.background = background
        self.foreground = foreground
        self._janela = None
        widget.bind("<Enter>", self._entrar, add="+")
        widget.bind("<Leave>", self._sair, add="+")
        widget.bind("<ButtonPress>", self._sair, add="+")

    def _entrar(self, _evento):
        if self._janela:
            return
        self._sair(None)
        texto = self.get_text()
        if not texto:
            return
        self._janela = tk.Toplevel(self.widget)
        self._janela.wm_overrideredirect(True)
        x = self.widget.winfo_rootx() + 8
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self._janela.wm_geometry(f"+{x}+{y}")
        rotulo = tk.Label(
            self._janela,
            text=texto,
            background=self.background,
            foreground=self.foreground,
            font=("Arial", 9),
            padx=8,
            pady=5,
            wraplength=280,
            justify="left",
        )
        rotulo.pack()
        self._janela.after(4000, self._sair)

    def _sair(self, _evento=None):
        if self._janela:
            self._janela.destroy()
            self._janela = None