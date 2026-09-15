import tkinter as tk
from tkinter import ttk, messagebox

from services.icms import (
    ALIQUOTA_INTERESTADUAL,
    ALIQUOTA_INTERNA,
    calcular_icms,
    formatar_moeda,
    function_aliquota,
)
from views.widgets import ToolTip

# ── Cores do TechStore (coírem com views/main_window.py) ────────
COR_HEADER_BG  = "#0f172a"
COR_HEADER_FG  = "#f8fafc"
COR_HEADER_SUB = "#94a3b8"
COR_AZUL       = "#1d4ed8"
COR_VERDE      = "#15803d"
COR_VERDE_HVR  = "#166534"
COR_VERDE_TEXTO = "#14532d"
COR_VERMELHO   = "#dc2626"
COR_FUNDO      = "#ffffff"
COR_FRAME      = "#ffffff"
COR_TEXTO      = "#0f172a"
COR_LABEL      = "#475569"
COR_BORDA      = "#cbd5e1"
PADX       = 20  # margem lateral padrão do TechStore

UFs_ORDENADAS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG",
    "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR",
    "RS", "SC", "SE", "SP", "TO",
]


class cadastro_window(tk.Toplevel):
    # (atributo do campo, rótulo amigável para o resumo de erros)
    CAMPOS = [
        ("entry_nome", "Nome"),
        ("entry_preco", "Preço"),
        ("combo_ufs", "UF de Origem/Destino"),
    ]
    ROTULOS = {
        "entry_nome": "Nome do Produto:",
        "entry_preco": "Preço (R$):",
    }

    def __init__(self, master, conexao=None, ao_cadastrado=None):
        super().__init__(master)
        self.conexao = conexao
        self.ao_cadastrado = ao_cadastrado or (lambda _novo_id: None)

        self.title("TechStore - Cadastro de Produtos")
        self.geometry("700x640")
        self.minsize(600, 560)
        self.configure(bg=COR_FUNDO)
        self.transient(master)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self._criar_widgets()
        self._atribuir_atalhos()

    # ── Atalhos de teclado (keyboard-first) ────────────────────────
    def _atribuir_atalhos(self):
        self.bind("<Control-Return>", lambda _e: self._cadastrar())
        self.bind("<Control-l>", lambda _e: self._limpar())
        self.bind("<Control-L>", lambda _e: self._limpar())
        self.bind("<Control-h>", lambda _e: self._ajuda())
        self.bind("<Control-H>", lambda _e: self._ajuda())
        self.bind("<Escape>", lambda _e: self.destroy())
        self.entry_preco.bind("<KeyRelease>", self._ao_digitar_preco)
        self.after(100, self.entry_nome.focus_set)

    def _ajuda(self):
        messagebox.showinfo(
            "Atalhos | Regra ICMS",
            "Atalhos de teclado\n"
            "──────────────────────────────────────\n"
            "Ctrl+Enter   Cadastrar produto\n"
            "Ctrl+L       Limpar formulário\n"
            "Ctrl+H       Abrir esta ajuda\n\n"
            "Regra de ICMS (TechStore)\n"
            "──────────────────────────────────────\n"
            "Mesma UF (SP → SP) ............ 18%\n"
            "UFs diferentes (SP → BA) ...... 7%\n\n"
            "valor_icms = preço base × (alíquota / 100)\n"
            "valor_total = preço base + valor_icms",
        )

    # ── Construção da interface ────────────────────────────────────
    def _criar_widgets(self):
        self._construir_header()

        # Corpo do formulário (margens e pesos como no TechStore)
        frame = tk.Frame(self, bg=COR_FRAME)
        frame.grid(row=1, column=0, sticky="nsew", padx=PADX, pady=(16, 8))
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)
        frame.columnconfigure(0, minsize=150)
        frame.columnconfigure(2, minsize=150)

        linha = 0
        linha = self._titulo_secao(frame, "DADOS DO PRODUTO", linha)
        linha = self._campo(frame, self.ROTULOS["entry_nome"], "entry_nome", linha)
        linha = self._campo(frame, self.ROTULOS["entry_preco"], "entry_preco", linha)
        tk.Label(
            frame, text="Ex.: 1.250,00 — utilise ponto ou vírgula como separador",
            font=("Arial", 8), bg=COR_FRAME, fg=COR_LABEL, anchor="w"
        ).grid(row=linha, column=1, columnspan=3, pady=(0, 0), sticky="w", padx=(0, 4))
        linha += 1

        linha = self._titulo_secao(
            frame, "TRIBUTAÇÃO — ICMS", linha,
            ("ICMS interno (mesma UF): 18%\n"
             "ICMS interestadual (UFs diferentes): 7%\n"
             "Ao informar UF de origem, UF de destino e preço,\n"
             "a alíquota, o valor do ICMS e o total são calculados."),
        )
        linha = self._campo_ufs(frame, linha)
        linha = self._campo_readonly(frame, "Alíquota ICMS (%):", "entry_aliq", linha)
        linha = self._campo_readonly(frame, "Valor ICMS (R$):", "entry_valor_icms", linha)
        linha = self._campo_readonly(frame, "Valor Total (R$):", "entry_valor_total", linha)

        # Mensagem de status (alerta info/erro/sucesso)
        self.lbl_status = tk.Label(
            frame, text="", font=("Arial", 10), bg=COR_FRAME, fg=COR_VERDE_TEXTO
        )
        self.lbl_status.grid(row=linha, column=0, columnspan=4, pady=(12, 0),
                             sticky="w", padx=(4, 0))
        linha += 1

        # Dica de atalhos (descoberta de teclado)
        tk.Label(
            frame, text="Ctrl+Enter cadastrar · Ctrl+L limpar · Ctrl+H atalhos",
            font=("Arial", 8), bg=COR_FRAME, fg=COR_LABEL, anchor="w"
        ).grid(row=linha, column=0, columnspan=4, pady=(2, 0), sticky="w", padx=(4, 0))
        linha += 1

        # Botões (alinhados à direita, padrão toolbar do TechStore)
        btn_frame = tk.Frame(frame, bg=COR_FRAME)
        btn_frame.grid(row=linha, column=0, columnspan=4, pady=(12, 16), sticky="e")

        tk.Button(
            btn_frame, text="Cadastrar", font=("Arial", 11, "bold"),
            bg=COR_VERDE, fg="#ffffff", activebackground=COR_VERDE_HVR,
            activeforeground="#ffffff", bd=0, cursor="hand2",
            command=self._cadastrar
        ).pack(side="left", padx=(0, 8), ipady=6, ipadx=14)

        tk.Button(
            btn_frame, text="Limpar", font=("Arial", 11),
            bg=COR_AZUL, fg="#ffffff", activebackground="#1e40af",
            activeforeground="#ffffff", bd=0, cursor="hand2",
            command=self._limpar
        ).pack(side="left", ipady=6, ipadx=14)

    def _construir_header(self):
        cab = tk.Frame(self, bg=COR_HEADER_BG, height=66)
        cab.grid(row=0, column=0, sticky="ew")
        cab.grid_propagate(False)
        cab.columnconfigure(0, weight=1)

        tk.Label(
            cab, text="TechStore", bg=COR_HEADER_BG, fg="#ffffff",
            font=("Arial", 17, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(PADX, 0), pady=(10, 0))
        tk.Label(
            cab, text="Cadastro de Produtos · validação de ICMS",
            bg=COR_HEADER_BG, fg=COR_HEADER_SUB, font=("Arial", 10),
        ).grid(row=1, column=0, sticky="w", padx=(PADX, 0), pady=(0, 12))

        tk.Frame(cab, bg=COR_AZUL, height=3).grid(row=2, column=0, sticky="ew")

    def _titulo_secao(self, parent, texto, linha, ajuda=""):
        rotulo = tk.Label(
            parent, text=texto, font=("Arial", 10, "bold"),
            bg=COR_FRAME, fg=COR_AZUL, anchor="w"
        )
        rotulo.grid(row=linha, column=0, columnspan=4, sticky="ew",
                    padx=(4, 0), pady=(16, 0))
        if ajuda:
            ToolTip(rotulo, lambda: ajuda)
        tk.Frame(parent, bg=COR_BORDA, height=1).grid(
            row=linha + 1, column=0, columnspan=4, sticky="ew", padx=(4, 0), pady=(2, 0)
        )
        return linha + 2

    def _combo(self, parent, largura=6):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground="#ffffff", background="#ffffff",
                        foreground=COR_TEXTO, selectbackground=COR_AZUL,
                        selectforeground="#ffffff", bordercolor=COR_BORDA,
                        lightcolor=COR_BORDA, darkcolor=COR_BORDA)
        return ttk.Combobox(parent, values=UFs_ORDENADAS, state="readonly",
                            font=("Arial", 10), width=largura)

    def _campo(self, parent, label_text, attr_name, linha):
        tk.Label(
            parent, text=label_text, font=("Arial", 10),
            bg=COR_FRAME, fg=COR_LABEL, anchor="w"
        ).grid(row=linha, column=0, sticky="w", padx=(4, 8), pady=(8, 0))

        entry = tk.Entry(
            parent, font=("Arial", 11), bg="#ffffff", fg=COR_TEXTO,
            insertbackground=COR_TEXTO, bd=0, relief="flat",
            highlightthickness=1, highlightbackground=COR_BORDA,
            highlightcolor=COR_AZUL
        )
        entry.grid(row=linha, column=1, columnspan=3, sticky="ew",
                   padx=(0, 4), pady=(8, 0), ipady=5)
        setattr(self, attr_name, entry)
        return linha + 1

    def _campo_ufs(self, parent, linha):
        tk.Label(
            parent, text="UF de Origem:", font=("Arial", 10),
            bg=COR_FRAME, fg=COR_LABEL, anchor="w"
        ).grid(row=linha, column=0, sticky="w", padx=(4, 8), pady=(8, 0))

        self.combo_origem = self._combo(parent)
        self.combo_origem.grid(row=linha, column=1, sticky="w", padx=(0, 16), pady=(8, 0))
        self.combo_origem.bind("<<ComboboxSelected>>", self._on_uf_change)
        ToolTip(self.combo_origem, lambda: "Estado de onde o produto sai (remetente).")

        tk.Label(
            parent, text="UF de Destino:", font=("Arial", 10),
            bg=COR_FRAME, fg=COR_LABEL, anchor="w"
        ).grid(row=linha, column=2, sticky="w", padx=(4, 8), pady=(8, 0))

        self.combo_destino = self._combo(parent)
        self.combo_destino.grid(row=linha, column=3, sticky="w", padx=(0, 4), pady=(8, 0))
        self.combo_destino.bind("<<ComboboxSelected>>", self._on_uf_change)
        ToolTip(self.combo_destino, lambda: "Estado para onde o produto vai (destinatário).")
        return linha + 1

    def _campo_readonly(self, parent, label_text, attr_name, linha):
        tk.Label(
            parent, text=label_text, font=("Arial", 10),
            bg=COR_FRAME, fg=COR_LABEL, anchor="w"
        ).grid(row=linha, column=0, sticky="w", padx=(4, 8), pady=(8, 0))

        entry = tk.Entry(
            parent, font=("Arial", 11, "bold"), bg="#f1f5f9",
            fg=COR_AZUL, bd=0, relief="flat", highlightthickness=1,
            highlightbackground=COR_BORDA, highlightcolor=COR_AZUL,
            state="readonly"
        )
        entry.grid(row=linha, column=1, columnspan=3, sticky="ew",
                   padx=(0, 4), pady=(8, 0), ipady=5)
        setattr(self, attr_name, entry)
        return linha + 1

    # ── Lógica de ICMS ─────────────────────────────────────────────
    def _calcular_icms(self):
        uf_origem = self.combo_origem.get()
        uf_destino = self.combo_destino.get()
        preco = self.entry_preco.get().strip()

        for attr in ("entry_aliq", "entry_valor_icms", "entry_valor_total"):
            self._resetar_entry(attr)

        if not (uf_origem and uf_destino):
            return

        aliq = function_aliquota(uf_origem, uf_destino)
        tipo = "operação interna" if aliq == float(ALIQUOTA_INTERNA) else "interestadual"

        self._escrever_readonly("entry_aliq", f"{aliq:.0f}%")

        self.lbl_status.configure(
            text=f"{uf_origem} → {uf_destino}: ICMS {aliq:.0f}% ({tipo})",
            fg=COR_AZUL
        )

        if not preco:
            self._escrever_readonly("entry_valor_icms", "informe o preço")
            self._escrever_readonly("entry_valor_total", "informe o preço")
            return

        try:
            base = float(preco.replace(",", "."))
            if base <= 0:
                raise ValueError
        except ValueError:
            self._escrever_readonly("entry_valor_icms", "preço inválido")
            self._escrever_readonly("entry_valor_total", "preço inválido")
            return

        icms = base * (aliq / 100)
        total = base + icms
        self._escrever_readonly("entry_valor_icms", f"R$ {icms:,.2f}")
        self._escrever_readonly("entry_valor_total", f"R$ {total:,.2f}")

    def _on_uf_change(self, _event=None):
        self._limpar_bordas()
        self._calcular_icms()

    def _ao_digitar_preco(self, _event=None):
        self._limpar_bordas()
        self._calcular_icms()

    # ── Suporte a campos readonly ──────────────────────────────────
    def _resetar_entry(self, attr):
        entry = getattr(self, attr)
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.configure(state="readonly")

    def _escrever_readonly(self, attr, texto):
        entry = getattr(self, attr)
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, texto)
        entry.configure(state="readonly")

    # ── Realce de campos (validação inline) ────────────────────────
    def _bordas(self, cor):
        for atr, _rotulo in self.CAMPOS:
            if hasattr(self, atr):
                getattr(self, atr).configure(highlightbackground=cor, highlightcolor=cor)

    def _limpar_bordas(self):
        for atr, _rotulo in self.CAMPOS:
            if hasattr(self, atr):
                getattr(self, atr).configure(
                    highlightbackground=COR_BORDA, highlightcolor=COR_AZUL
                )

    def _bordas_sucesso(self):
        self._bordas(COR_VERDE)

    # ── Cadastro ───────────────────────────────────────────────────
    def _cadastrar(self):
        self.lbl_status.configure(text="")
        self._limpar_bordas()

        nome   = self.entry_nome.get().strip()
        preco  = self.entry_preco.get().strip()
        origem = self.combo_origem.get()
        destino = self.combo_destino.get()

        erros = []
        mensagens = []
        if not nome:
            erros.append("entry_nome")
            mensagens.append("Nome: campo obrigatório")
        if not preco:
            erros.append("entry_preco")
            mensagens.append("Preço: informe um valor maior que zero")
        else:
            try:
                preco_val = float(preco.replace(",", "."))
                if preco_val <= 0:
                    raise ValueError
            except ValueError:
                erros.append("entry_preco")
                mensagens.append("Preço: informe um valor numérico positivo")
        if not origem or not destino:
            erros.append("combo_ufs")
            mensagens.append("UFs: selecione origem e destino")

        if erros:
            for atr in erros:
                if atr == "combo_ufs":
                    continue
                getattr(self, atr).configure(
                    highlightbackground=COR_VERMELHO, highlightcolor=COR_VERMELHO
                )
            self.lbl_status.configure(
                text=" · ".join(mensagens) + ".",
                fg=COR_VERMELHO,
            )
            for atr in erros:
                if atr != "combo_ufs":
                    getattr(self, atr).focus_set()
                    break
            return

        preco_float = float(preco.replace(",", "."))

        calc = calcular_icms({
            "uf_origem": origem,
            "uf_destino": destino,
            "valor_base": preco_float,
            "valor_icms": 0,
            "aliquota_icms": 0,
        })
        aliq = float(calc["aliquota"])
        valor_icms = float(calc["valor_icms"])
        valor_total = float(calc["valor_total"])
        tipo = "operação interna" if aliq == float(ALIQUOTA_INTERNA) else "interestadual"

        if self.conexao is None:
            self._exibir_sucesso(
                nome, preco_float, origem, destino, aliq, valor_icms, valor_total, tipo
            )
            return

        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            novo_id = self.conexao.inserir_produto(
                nome, origem, destino,
                preco_float, aliq, valor_icms, valor_total,
            )
        finally:
            self.configure(cursor="")
        if novo_id is None:
            messagebox.showerror(
                "Erro no cadastro",
                "Não foi possível gravar o produto no banco de dados.\n"
                "Verifique a conexão com o MySQL e tente novamente.",
                parent=self,
            )
            return

        self._exibir_sucesso(
            nome, preco_float, origem, destino, aliq, valor_icms, valor_total, tipo
        )
        self.ao_cadastrado(novo_id)

    def _exibir_sucesso(
        self, nome, preco_float, origem, destino, aliq, valor_icms, valor_total, tipo
    ):
        messagebox.showinfo(
            "Cadastro realizado",
            f"Produto cadastrado com sucesso!\n\n"
            f"Nome:          {nome}\n"
            f"Preço base:    {formatar_moeda(preco_float)}\n"
            f"Rota:          {origem} → {destino}\n"
            f"ICMS:          {aliq:.0f}% ({tipo})\n"
            f"Valor ICMS:    {formatar_moeda(valor_icms)}\n"
            f"Valor Total:   {formatar_moeda(valor_total)}",
            parent=self,
        )

        self._limpar()
        self._bordas_sucesso()
        self.lbl_status.configure(
            text="Produto cadastrado com sucesso!", fg=COR_VERDE_TEXTO
        )
        self.after(3000, self._limpar_bordas)

    def _limpar(self):
        for atr, _rotulo in self.CAMPOS:
            if hasattr(self, atr):
                getattr(self, atr).delete(0, "end")
        for atr in ("entry_aliq", "entry_valor_icms", "entry_valor_total"):
            self._resetar_entry(atr)
        self.combo_origem.set("")
        self.combo_destino.set("")
        self.lbl_status.configure(text="")
        self._limpar_bordas()
        self.entry_nome.focus_set()


def executar(conexao=None, ao_cadastrado=None):
    root = tk.Tk()
    app = cadastro_window(root, conexao=conexao, ao_cadastrado=ao_cadastrado)
    app.mainloop()


if __name__ == "__main__":
    from DB.conexao import DB_CONFIG, conexao

    executar(conexao=conexao(**DB_CONFIG))