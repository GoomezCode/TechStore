# Mini Hackathon: TechStore

**Operação Fechamento Fiscal - Auditoria e correção de ICMS no banco de dados**

---

## 1. A História

Sexta-feira, 18h. Véspera do fechamento do mês.

A Ana, analista fiscal da **TechStore**, abre o sistema para fechar o relatório de impostos do mês e leva um susto: todas as vendas estão com o ICMS calculado errado.

O estagiário que rodou a carga inicial do banco usou a alíquota de São Paulo (18%) em produtos que saíram de SP para outros estados quando o correto é 7% (regra de ICMS interestadual).

> **Resultado:** a empresa recolheu imposto a mais em cima de vendas reais. A contabilidade já foi notificada e o diretor quer a correção até segunda-feira.

**Sua missão:** criar uma tela única que conecta no banco, recalcula o ICMS correto e regrava os dados.

---

## 2. O Desafio

Criar uma aplicação Tkinter com UMA tela que:

1. Conecta no banco `techstore`
2. Mostra os produtos com ICMS errado numa Treeview
3. Tem UM botão: **Corrigir ICMS**
4. Ao clicar, roda o UPDATE no banco e atualiza a lista na tela

*Um botão. Uma ação. Um resultado.*

---

## 3. O Banco de Dados

```sql
CREATE DATABASE techstore CHARACTER SET utf8mb4;
USE techstore;

CREATE TABLE produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    uf_origem CHAR(2) NOT NULL,
    uf_destino CHAR(2) NOT NULL,
    valor_base DECIMAL(10,2) NOT NULL,
    aliquota_icms DECIMAL(5,2) NOT NULL,
    valor_icms DECIMAL(10,2) NOT NULL,
    valor_total DECIMAL(10,2) NOT NULL
);

INSERT INTO produtos
(nome, uf_origem, uf_destino, valor_base, aliquota_icms, valor_icms, valor_total)
VALUES
('Notebook Dell', 'SP', 'BA', 3500.00, 18.00, 630.00, 4130.00),
('Monitor LG', 'SP', 'PE', 1200.00, 18.00, 216.00, 1416.00),
('Teclado Mecanico', 'SP', 'AM', 450.00, 18.00, 81.00, 531.00),
('Mouse Sem Fio', 'SP', 'CE', 89.90, 18.00, 16.18, 106.08),
('Impressora HP', 'MG', 'BA', 780.00, 18.00, 140.40, 920.40),
('HD Externo', 'RJ', 'AM', 320.00, 18.00, 57.60, 377.60),
('Roteador TP-Link', 'SP', 'GO', 210.00, 18.00, 37.80, 247.80),
('Webcam Logitech', 'PR', 'BA', 299.00, 18.00, 53.82, 352.82),
('Cadeira Gamer', 'SP', 'SP', 899.90, 18.00, 161.98, 1061.88),
('Estabilizador', 'SP', 'SP', 180.00, 18.00, 32.40, 212.40);
```

*O erro do estagiário: aplicou 18% em tudo, sem considerar a regra de ICMS interestadual.*

---

## 4. Entendendo as Alíquotas de ICMS

### O que é ICMS?

O ICMS é um imposto estadual aplicado sobre a venda de produtos. O valor da alíquota depende do trajeto da mercadoria — ou seja, de onde ela sai (origem) e para onde ela vai (destino).

### Tabela de Alíquotas (SOMENTE o que será usado no desafio)

| Situação da Venda | Alíquota | Exemplo |
|---|---|---|
| Mesma UF (origem = destino) | 18% | SP → SP |
| UFs diferentes (origem ≠ destino) | 7% | SP → BA, SP → PE, SP → AM |

É só isso. No nosso desafio existem apenas dois casos possíveis:

- Produto sai e chega no mesmo estado → 18%
- Produto sai de um estado e vai para outro → 7%

### Fórmula do Cálculo

- `valor_icms = valor_base x (aliquota / 100)`
- `valor_total = valor_base + valor_icms`

### Exemplos práticos (com os produtos do banco)

| Produto | Rota | Base | Alíq. correta | ICMS correto | Total correto |
|---|---|---|---|---|---|
| Notebook Dell | SP → BA | 3500,00 | 7% | 245,00 | 3745,00 |
| Monitor LG | SP → PE | 1200,00 | 7% | 84,00 | 1284,00 |
| Cadeira Gamer | SP → SP | 899,90 | 18% | 161,98 | 1061,88 |
| Estabilizador | SP → SP | 180,00 | 18% | 32,40 | 212,40 |

---

## 5. A Regra de Correção (para o código)

```
SE uf_origem == uf_destino
    -> aliquota = 18%
SENAO
    -> aliquota = 7%
```

---

## 6. SQL que você vai precisar

**1) Ler os produtos:**

```sql
SELECT id, nome, uf_origem, uf_destino, valor_base, aliquota_icms,
valor_icms, valor_total
FROM produtos;
```

**2) Gravar a correção (para cada produto):**

```sql
UPDATE produtos
SET aliquota_icms = %s,
    valor_icms = %s,
    valor_total = %s
WHERE id = %s;
```

**3) Conferir se sobrou erro:**

```sql
SELECT COUNT(*) FROM produtos
WHERE aliquota_icms = 18 AND uf_origem <> uf_destino;
-- deve retornar 0
```

---

## 7. Dicas Importantes

- **Duplique a tabela antes de testar!** Em vez de fazer backup em arquivo com mysqldump, crie uma cópia da tabela dentro do próprio banco. Assim, se algo der errado, você restaura rapidinho com um simples INSERT SELECT.
  - *Para duplicar a tabela:* `CREATE TABLE produtos_backup AS SELECT * FROM produtos;`
  - *Conferir se copiou tudo:* `SELECT COUNT(*) FROM produtos_backup;` (deve retornar 10)
  - *Se algo der errado, RESTAURAR:* `TRUNCATE TABLE produtos; INSERT INTO produtos SELECT * FROM produtos_backup;`
  - *Quando tiver certeza que está tudo certo:* `DROP TABLE produtos_backup;`
- **Nunca use UPDATE sem WHERE.** Sempre `WHERE id = %s`.
- **Teste num SELECT antes:** rode `SELECT id, valor_base * 0.07 FROM produtos WHERE uf_origem <> uf_destino` pra conferir os valores antes de gravar.
- **conn.commit() é obrigatório.** Sem ele, nada é gravado no banco.
- **Confirmação antes de corrigir:** nunca deixe um botão alterar o banco sem perguntar ao usuário.
- **Use try/except em volta do banco:** se cair a conexão, o programa não pode travar.

---

## 8. Resultado Esperado (Checklist Final)

Depois de clicar no botão, o aluno deve conferir:

| Produto | Rota | ICMS antes | ICMS depois | Mudou? |
|---|---|---|---|---|
| Notebook Dell | SP → BA | 630,00 | 245,00 | Sim |
| Monitor LG | SP → PE | 216,00 | 84,00 | Sim |
| Teclado Mecânico | SP → AM | 81,00 | 31,50 | Sim |
| Cadeira Gamer | SP → SP | 161,98 | 161,98 | Não (já correto) |
| Estabilizador | SP → SP | 32,40 | 32,40 | Não (já correto) |
