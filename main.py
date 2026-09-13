from DB.conexao import conexao, DB_CONFIG
from views.main_window import main_window

conecta = conexao(**DB_CONFIG)

main_window(conecta)