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
(nome, uf_origem, uf_destino, valor_base, aliquota_icms, valor_icms,
valor_total)
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