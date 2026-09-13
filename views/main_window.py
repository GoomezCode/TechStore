import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from services.icms import (
    function_aliquota,
    calcular_icms,
    formatar_moeda,
    formatar_numero,
)
from views.widgets import ToolTip

COR_HEADER_BG = "#0f172a"
COR_HEADER_FG = "#f8fafc"

COLUNAS = [
    # (chave, rotulo, largura, ancora, esticar)
    ("nome", "Produto", 260, "w", True),
    ("uf_origem", "UF Origem", 90, "center", False),
    ("uf_destino", "UF Destino", 90, "center", False),
    ("valor_base", "Valor Base", 120, "e", False),
    ("aliquota_icms", "Alíq. ICMS %", 100, "e", False),
    ("valor_icms", "Valor ICMS", 120, "e", False),
    ("valor_total", "Valor Total", 130, "e", False),
]
COLUNAS_NUMERICAS = {"valor_base", "valor_icms", "valor_total", "aliquota_icms"}

CHECKLIST_COLUNAS = [
    # (chave, rotulo, largura, ancora, esticar)
    ("produto", "Produto", 260, "w", True),
    ("rota", "Rota", 130, "center", False),
    ("icms_antes", "ICMS antes", 130, "e", False),
    ("icms_depois", "ICMS depois", 130, "e", False),
    ("mudou", "Mudou?", 150, "center", False),
]


class main_window:
    def __init__(self, conexao):
        self.conexao = conexao
        self._conectado = self.conexao.conectar()

        self.window = tk.Tk()
        self.window.title("TechStore — Fechamento Fiscal")
        self.window.geometry("1280x720")
        self.window.minsize(1024, 600)
        self.window.configure(bg="#ffffff")
        self.window.rowconfigure(4, weight=1)
        self.window.columnconfigure(0, weight=1)

        self._linhas = []
        self._filtro_var = tk.StringVar()
        self._ordem = {"coluna": None, "reversa": False}
        self._modo_checklist = False
        self._checklist = None

        self._configurar_estilo()
        self._construir_header()
        self._construir_kpis()
        self._construir_toolbar()
        self._construir_banner()
        self._construir_tabela()
        self._construir_status()

        self.window.bind("<Control-f>", lambda _e: self._focar_busca())
        self.window.bind("<Control-l>", lambda _e: self._focar_busca())
        self.window.bind("<Control-r>", lambda _e: self._corrigir_icms())
        self.window.bind("<Control-i>", lambda _e: self._alternar_checklist())
        self.window.protocol("WM_DELETE_WINDOW", self._fechar)

        self._carregar_dados()
        self.btn_corrigir.focus_set()
        self.window.mainloop()

    # ------------------------------------------------------------------ UI

    def _configurar_estilo(self):
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure(
            "Tech.Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#0f172a",
            rowheight=38,
            borderwidth=0,
            font=("Arial", 10),
        )
        estilo.configure(
            "Tech.Treeview.Heading",
            background="#f1f5f9",
            foreground="#0f172a",
            font=("Arial", 10, "bold"),
            relief="flat",
            padding=(8, 7),
        )
        estilo.map(
            "Tech.Treeview",
            background=[("selected", "#bfdbfe")],
            foreground=[("selected", "#0f172a")],
        )
        estilo.map("Tech.Treeview.Heading", background=[("active", "#e2e8f0")])
        estilo.configure(
            "Tech.TButton",
            background="#16a34a",
            foreground="#ffffff",
            font=("Arial", 11, "bold"),
            padding=(20, 11),
            relief="flat",
        )
        estilo.map(
            "Tech.TButton",
            background=[("active", "#15803d"), ("disabled", "#cbd5e1")],
            foreground=[("disabled", "#f1f5f9")],
        )
        estilo.configure(
            "Tech.TEntry", fieldbackground="#f8fafc", bordercolor="#cbd5e1"
        )

    def _construir_header(self):
        cab = tk.Frame(self.window, bg=COR_HEADER_BG, height=66)
        cab.grid(row=0, column=0, sticky="ew")
        cab.grid_propagate(False)
        cab.columnconfigure(0, weight=1)

        tk.Label(
            cab, text="TechStore", bg=COR_HEADER_BG, fg="#ffffff",
            font=("Arial", 17, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(20, 0), pady=(10, 0))
        tk.Label(
            cab, text="Operação Fechamento Fiscal · Auditoria e correção de ICMS",
            bg=COR_HEADER_BG, fg="#94a3b8", font=("Arial", 10),
        ).grid(row=1, column=0, sticky="w", padx=(20, 0), pady=(0, 12))

        tk.Frame(cab, bg="#1d4ed8", height=3).grid(row=2, column=0, sticky="ew")

    def _construir_kpis(self):
        linha = tk.Frame(self.window, bg="#ffffff")
        linha.grid(row=1, column=0, sticky="ew", padx=20, pady=(16, 4))
        linha.columnconfigure((0, 1, 2), weight=1, uniform="kpi")

        self._kpi_palavras = {}
        specs = [
            ("total", "Produtos", "#2563eb"),
            ("erros", "ICMS incorreto", "#d97706"),
            ("impacto", "Impacto da correção", "#dc2626"),
        ]
        for col, (chave, rotulo, cor) in enumerate(specs):
            cartao = tk.Frame(
                linha, bg="#ffffff", highlightbackground="#e2e8f0",
                highlightthickness=1,
            )
            cartao.grid(row=0, column=col, sticky="nsew", padx=(0, 12) if col < 2 else 0)
            tk.Frame(cartao, bg=cor, height=4).pack(fill="x")
            corpo = tk.Frame(cartao, bg="#ffffff")
            corpo.pack(fill="both", expand=True, padx=14, pady=(10, 12))
            tk.Label(
                corpo, text=rotulo.upper(), bg="#ffffff", fg="#64748b",
                font=("Arial", 9, "bold"),
            ).pack(anchor="w")
            valor = tk.Label(
                corpo, text="—", bg="#ffffff", fg=cor,
                font=("Arial", 24, "bold"),
            )
            valor.pack(anchor="w", pady=(2, 0))
            self._kpi_palavras[chave] = valor

    def _construir_toolbar(self):
        barra = tk.Frame(self.window, bg="#ffffff")
        barra.grid(row=2, column=0, sticky="ew", padx=20, pady=(8, 0))
        barra.columnconfigure(1, weight=1)

        tk.Label(
            barra, text="Buscar", bg="#ffffff", fg="#475569",
            font=("Arial", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.entry_busca = ttk.Entry(
            barra, textvariable=self._filtro_var, width=32, style="Tech.TEntry"
        )
        self.entry_busca.grid(row=0, column=1, sticky="w")
        self.entry_busca.bind("<Escape>", self._limpar_busca)
        self._filtro_var.trace_add("write", lambda *_a: self._renderizar_tabela())

        self.btn_corrigir = ttk.Button(
            barra, text="Corrigir ICMS", style="Tech.TButton",
            command=self._corrigir_icms,
        )
        self.btn_corrigir.grid(row=0, column=2, sticky="e")
        self.btn_corrigir.bind("<Return>", lambda _e: self._corrigir_icms())
        self.btn_tooltip = ToolTip(
            self.btn_corrigir, self._texto_tooltip_botao
        )

        self.btn_checklist = ttk.Button(
            barra, text="Checklist", command=self._alternar_checklist
        )
        self.btn_checklist.state(["disabled"])
        self.btn_checklist.grid(row=0, column=3, sticky="e", padx=(12, 0))
        self.btn_checklist_tooltip = ToolTip(
            self.btn_checklist, self._texto_tooltip_checklist
        )

    def _construir_banner(self):
        self.banner = tk.Label(
            self.window, text="", bg="#dcfce7", fg="#166534",
            font=("Arial", 10, "bold"), padx=12, pady=7, anchor="w",
            justify="left",
        )

    def _configurar_colunas(self, colunas_espec, ordena):
        ids = tuple(col[0] for col in colunas_espec)
        self.tree.configure(columns=ids)
        for chave, rotulo, largura, ancora, esticar in colunas_espec:
            if ordena:
                self.tree.heading(
                    chave, text=rotulo,
                    command=lambda c=chave: self._ordenar(c),
                )
            else:
                self.tree.heading(chave, text=rotulo)
            self.tree.column(
                chave, width=largura, anchor=ancora, stretch=esticar
            )

    def _construir_tabela(self):
        self.frame_tabela = tk.Frame(self.window, bg="#ffffff")
        self.frame_tabela.grid(row=4, column=0, sticky="nsew", padx=20, pady=12)
        self.frame_tabela.rowconfigure(0, weight=1)
        self.frame_tabela.columnconfigure(0, weight=1)

        colunas_id = tuple(col[0] for col in COLUNAS)
        self.tree = ttk.Treeview(
            self.frame_tabela, columns=colunas_id, show="headings",
            style="Tech.Treeview",
        )
        self._configurar_colunas(COLUNAS, ordena=True)
        self.tree.tag_configure("impar", background="#ffffff")
        self.tree.tag_configure("par", background="#f8fafc")

        scroll_y = ttk.Scrollbar(
            self.frame_tabela, orient="vertical", command=self.tree.yview
        )
        scroll_x = ttk.Scrollbar(
            self.frame_tabela, orient="horizontal", command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        self.label_vazio = tk.Label(
            self.frame_tabela, text="", bg="#ffffff", fg="#64748b",
            font=("Arial", 12), justify="center",
        )
        self.label_vazio.grid(row=0, column=0, sticky="nsew")
        self.label_vazio.grid_forget()  # sobe apenas quando preciso

    def _construir_status(self):
        barra = tk.Frame(self.window, bg="#f8fafc", height=30)
        barra.grid(row=5, column=0, sticky="ew")
        barra.grid_propagate(False)
        barra.columnconfigure(0, weight=1)

        self.dot = tk.Label(barra, text="●", bg="#f8fafc", fg="#94a3b8",
                            font=("Arial", 10), width=2)
        self.dot.pack(side="left", padx=(16, 0), pady=6)
        self.status_conexao = tk.Label(
            barra, text="Conectando…", bg="#f8fafc", fg="#475569",
            font=("Arial", 9),
        )
        self.status_conexao.pack(side="left", padx=(0, 8))
        self.status_detalhe = tk.Label(
            barra, text="", bg="#f8fafc", fg="#94a3b8", font=("Arial", 9),
        )
        self.status_detalhe.pack(side="right", padx=16)

    # ------------------------------------------------------------- métodos

    def function_aliquota(self, uf_origem, uf_destino):
        return function_aliquota(uf_origem, uf_destino)

    def _carregar_dados(self):
        self._linhas = []
        if not self._conectado:
            self._atualizar_estado_conexao(False)
        else:
            try:
                resultado = self.conexao.consulta_produto()
                chaves = ("id", "nome", "uf_origem", "uf_destino",
                          "valor_base", "aliquota_icms", "valor_icms",
                          "valor_total")
                self._linhas = [dict(zip(chaves, linha)) for linha in resultado]
                self._atualizar_estado_conexao(True)
                self._atualizar_ordem_inicial()
            except Exception as e:
                print(f"Error: {e}")
                self._atualizar_estado_conexao(False)
        self._atualizar_kpis()
        self._renderizar_tabela()
        self._atualizar_status("carregado")

    def _atualizar_ordem_inicial(self):
        if self._ordem["coluna"] is None and self._linhas:
            self._ordem = {"coluna": "nome", "reversa": False}
        elif not self._linhas:
            self._ordem = {"coluna": None, "reversa": False}

    def _atualizar_estado_conexao(self, conectado):
        self._conectado = conectado
        if conectado:
            self.dot.configure(fg="#16a34a")
            self.status_conexao.configure(text="Conectado ao banco techstore")
        else:
            self.dot.configure(fg="#dc2626")
            self.status_conexao.configure(text="Sem conexão com o banco de dados")

    def _atualizar_kpis(self):
        calculos = [calcular_icms(l) for l in self._linhas]
        erros = sum(1 for c in calculos if c["incorreto"])
        impacto = sum(
            float(c["atual"] - c["valor_icms"])
            for c in calculos if c["incorreto"]
        )
        self._kpi_palavras["total"].configure(text=str(len(self._linhas)))
        self._kpi_palavras["erros"].configure(text=str(erros))
        self._kpi_palavras["impacto"].configure(text=formatar_moeda(impacto))
        self._atualizar_botao_estado(erros > 0)

    def _atualizar_botao_estado(self, pode_corrigir):
        if not self._conectado:
            self.btn_corrigir.state(["disabled"])
        elif pode_corrigir:
            self.btn_corrigir.state(["!disabled"])
        else:
            self.btn_corrigir.state(["disabled"])

    def _texto_tooltip_botao(self):
        if not self._conectado:
            return "Não há conexão com o banco de dados. Verifique a rede e reinicie a aplicação."
        if any(calcular_icms(l)["incorreto"] for l in self._linhas):
            return (
                "Recalcula a alíquota (18% dentro da mesma UF, 7% "
                "interestadual), atualiza valor de ICMS e total de todos os "
                "produtos incorretos e regrava o banco."
            )
        return "Nenhum produto com ICMS incorreto: nada a corrigir (Ctrl+R)."

    def _renderizar_tabela(self):
        self.tree.delete(*self.tree.get_children())
        filtro = self._filtro_var.get().strip().casefold()

        if self._modo_checklist:
            self._configurar_colunas(CHECKLIST_COLUNAS, ordena=False)
            linhas = self._checklist or []
            if filtro:
                linhas = [
                    c for c in linhas
                    if filtro in str(c["nome"]).casefold()
                ]
            for i, c in enumerate(linhas):
                tag = "impar" if i % 2 == 0 else "par"
                self.tree.insert(
                    "", "end",
                    values=(
                        c["nome"],
                        c["rota"],
                        formatar_moeda(c["icms_antes"]),
                        formatar_moeda(c["icms_depois"]),
                        c["mudou"],
                    ),
                    tags=(tag,),
                )
            self._mostrar_estado_tabela(linhas)
            return

        self._configurar_colunas(COLUNAS, ordena=True)
        linhas = self._linhas
        if filtro:
            linhas = [
                l for l in linhas
                if filtro in l["nome"].casefold()
                or filtro in l["uf_origem"].casefold()
                or filtro in l["uf_destino"].casefold()
            ]

        col_atual = self._ordem["coluna"]
        if col_atual:
            numerica = col_atual in COLUNAS_NUMERICAS

            def chave_ordenacao(linha):
                valor = linha[col_atual]
                return float(valor) if numerica else str(valor).casefold()

            linhas.sort(
                key=chave_ordenacao, reverse=self._ordem["reversa"]
            )

        for i, l in enumerate(linhas):
            tag = "impar" if i % 2 == 0 else "par"
            self.tree.insert(
                "", "end",
                values=(
                    l["nome"],
                    l["uf_origem"],
                    l["uf_destino"],
                    formatar_moeda(l["valor_base"]),
                    formatar_numero(l["aliquota_icms"]) + "%",
                    formatar_moeda(l["valor_icms"]),
                    formatar_moeda(l["valor_total"]),
                ),
                tags=(tag,),
            )
        self._atualizar_indicadores_ordem()

        self._mostrar_estado_tabela(linhas)

    def _mostrar_estado_tabela(self, linhas):
        if self._modo_checklist:
            if self._checklist is None:
                msg = ("Nenhuma correção realizada ainda.\n\n"
                       "Clique em \"Corrigir ICMS\" para gerar o comparativo.")
            elif not linhas:
                msg = "Nenhum produto corresponde à busca."
            else:
                msg = ""
        elif not self._linhas:
            if self._conectado:
                msg = ("Nenhum produto no banco de dados.\n\n"
                       "Cadastre produtos para iniciar a auditoria de ICMS.")
            else:
                msg = ("Não foi possível conectar ao banco de dados.\n\n"
                       "Verifique a conexão de rede e tente novamente.")
        elif not linhas:
            msg = "Nenhum produto corresponde à busca."
        else:
            msg = ""
        if msg:
            self.label_vazio.configure(text=msg)
            self.label_vazio.grid()
            self.label_vazio.tkraise()
        else:
            self.label_vazio.grid_forget()

    def _atualizar_indicadores_ordem(self):
        if self._modo_checklist:
            return
        for chave, rotulo, *_resto in COLUNAS:
            texto = rotulo
            if self._ordem["coluna"] == chave:
                texto += " ▼" if self._ordem["reversa"] else " ▲"
            self.tree.heading(chave, text=texto)

    def _ordenar(self, coluna):
        if self._modo_checklist:
            return
        reversa = False
        if self._ordem["coluna"] == coluna:
            reversa = not self._ordem["reversa"]
        self._ordem = {"coluna": coluna, "reversa": reversa}
        self._renderizar_tabela()

    def _focar_busca(self):
        self.entry_busca.focus_set()
        self.entry_busca.selection_range(0, "end")

    def _limpar_busca(self, _evento=None):
        self._filtro_var.set("")
        self.btn_corrigir.focus_set()

    # --------------------------------------------------------- correção

    def _corrigir_icms(self):
        if not self._conectado:
            messagebox.showerror(
                "Sem conexão",
                "Não há conexão com o banco de dados.\n"
                "Verifique a rede e reinicie a aplicação.",
            )
            return

        erros = [l for l in self._linhas if calcular_icms(l)["incorreto"]]
        if not erros:
            messagebox.showinfo(
                "Nada a corrigir",
                "Todos os produtos já estão com a alíquota de ICMS correta.",
            )
            return

        ja_ok = len(self._linhas) - len(erros)
        impacto = sum(
            float(calcular_icms(l)["atual"] - calcular_icms(l)["valor_icms"])
            for l in erros
        )
        msg = (
            f"{len(erros)} produto(s) com ICMS incorreto serão corrigidos.\n"
            f"{ja_ok} produto(s) já estão corretos e não serão alterados.\n\n"
            f"Impacto total da correção: {formatar_moeda(impacto)}\n\n"
            "Deseja continuar?"
        )
        if not messagebox.askyesno(
            "Confirmar correção", msg, icon="warning", parent=self.window
        ):
            return

        correcoes = []
        for l in erros:
            calc = calcular_icms(l)
            correcoes.append(
                (
                    float(calc["aliquota"]),
                    float(calc["valor_icms"]),
                    float(calc["valor_total"]),
                    int(l["id"]),
                )
            )

        self.btn_corrigir.state(["disabled"])
        self.window.configure(cursor="watch")
        self.window.update_idletasks()
        try:
            n = self.conexao.aplicar_correcoes(correcoes)
            if n != len(correcoes):
                raise RuntimeError(
                    f"Foram alterados apenas {n} de {len(correcoes)} registros."
                )
            self._checklist = self._gerar_checklist()
            self._modo_checklist = True
            self._atualizar_botao_checklist()
            self._carregar_dados()
            self._exibir_resumo(
                f"{len(erros)} produto(s) corrigido(s) · {ja_ok} já estavam corretos"
            )
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror(
                "Erro na correção",
                f"Não foi possível aplicar a correção.\n{e}",
                parent=self.window,
            )
        finally:
            self.btn_corrigir.focus_set()
            self.window.configure(cursor="")

    def _gerar_checklist(self):
        itens = []
        for l in self._linhas:
            calc = calcular_icms(l)
            antes = float(l["valor_icms"])
            depois = float(calc["valor_icms"])
            mudou = "Sim" if abs(antes - depois) > 0.005 else "Não (já correto)"
            itens.append({
                "nome": l["nome"],
                "rota": f"{str(l['uf_origem']).strip()} → {str(l['uf_destino']).strip()}",
                "icms_antes": antes,
                "icms_depois": depois,
                "mudou": mudou,
            })
        return itens

    def btn_corrigirICMS(self):
        self._corrigir_icms()

    def _exibir_resumo(self, texto):
        self.banner.configure(text=texto)
        self.banner.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 0))
        self.banner.after(6000, self.banner.grid_forget)

    def _alternar_checklist(self, _evento=None):
        if self._checklist is None:
            return
        self._modo_checklist = not self._modo_checklist
        self._atualizar_botao_checklist()
        self._renderizar_tabela()
        if self._modo_checklist:
            self.btn_checklist.focus_set()

    def _atualizar_botao_checklist(self):
        disponivel = self._conectado and self._checklist is not None
        self.btn_checklist.state(
            ["!disabled"] if disponivel else ["disabled"]
        )
        self.btn_checklist.configure(
            text="Voltar" if self._modo_checklist else "Checklist"
        )

    def _texto_tooltip_checklist(self):
        if self._checklist is None:
            return "O comparativo fica disponível depois de corrigir o ICMS."
        if self._modo_checklist:
            return "Volta à listagem completa de produtos."
        return "Exibe o comparativo ICMS antes/depois da última correção (Ctrl+I)."

    # ------------------------------------------------------ formatação

    def _atualizar_status(self, origem):
        agora = datetime.now().strftime("%H:%M:%S")
        if self._conectado:
            total = len(self._linhas)
            texto = f"{total} produto(s) · atualizado às {agora}"
        else:
            texto = f"última tentativa às {agora}"
        self.status_detalhe.configure(text=texto)

    def _fechar(self):
        if hasattr(self.conexao, "fechar"):
            self.conexao.fechar()
        self.window.destroy()