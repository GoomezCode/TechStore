import pymysql


# ── CONFIGURAÇÃO DO BANCO DE DADOS ──────────────────────────────
# Altere os valores abaixo conforme o seu ambiente.
DB_CONFIG = {
    "host": "192.168.68.63",   # IP do servidor MySQL
    "port": 3306,                # porta padrão do MySQL
    "user": "Senac",             # usuário do banco
    "password": "Senac@123",     # senha do banco
    "db": "techstore",           # nome do banco de dados
}
# ────────────────────────────────────────────────────────────────


class conexao:
    def __init__(self, host, db, user, password, port):
        self.host = host
        self.db = db
        self.user = user
        self.password = password
        self.port = port
        self.conexao = None

    def conectar(self):
        try:
            self.conexao = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.db,
                charset="utf8mb4",
            )
            return True
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return False

    def esta_conectado(self):
        return bool(self.conexao) and self.conexao.open

    def _garantir_conexao(self):
        if not self.esta_conectado():
            return self.conectar()
        return True

    def fechar(self):
        if self.esta_conectado():
            try:
                self.conexao.close()
            except pymysql.MySQLError:
                pass
        self.conexao = None

    def consulta_produto(self):
        sql = """select id, nome, uf_origem, uf_destino, valor_base,
                 aliquota_icms, valor_icms, valor_total
                 from produtos
                 order by nome;"""
        if not self._garantir_conexao():
            return []
        try:
            with self.conexao.cursor() as cursor:
                cursor.execute(sql)
                return cursor.fetchall()
        except pymysql.MySQLError as e:
            print(f"Error: {e}")
            return []

    def inserir_produto(
        self, nome, uf_origem, uf_destino, valor_base,
        aliquota_icms, valor_icms, valor_total
    ):
        """Insere um novo produto na tabela produtos.

        Retorna o id do registro criado ou None em caso de erro.
        """
        sql = """insert into produtos
                 (nome, uf_origem, uf_destino, valor_base, aliquota_icms,
                  valor_icms, valor_total)
                 values (%s, %s, %s, %s, %s, %s, %s)"""
        if not self._garantir_conexao():
            return None
        try:
            with self.conexao.cursor() as cursor:
                cursor.execute(
                    sql,
                    (nome, uf_origem, uf_destino, valor_base, aliquota_icms,
                     valor_icms, valor_total),
                )
                novo_id = cursor.lastrowid
            self.conexao.commit()
            return novo_id
        except pymysql.MySQLError as e:
            self.conexao.rollback()
            print(f"Error: {e}")
            return None

    def aplicar_correcoes(self, correcoes):
        """Aplica várias correções de ICMS em uma única transação.

        correcoes: lista de tuplas (aliquota_icms, valor_icms, valor_total, id).
        Retorna o número de registros alterados.
        """
        sql = """update produtos
                 set aliquota_icms = %s,
                     valor_icms = %s,
                     valor_total = %s
                 where id = %s"""
        if not correcoes:
            return 0
        if not self._garantir_conexao():
            return 0
        try:
            with self.conexao.cursor() as cursor:
                cursor.executemany(sql, correcoes)
                n = cursor.rowcount
            self.conexao.commit()
            return n
        except pymysql.MySQLError as e:
            self.conexao.rollback()
            print(f"Error: {e}")
            return 0
