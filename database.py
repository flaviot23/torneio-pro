import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    
    # Tabela de Configurações Gerais (Nome do Torneio)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM configuracoes WHERE chave = 'nome_torneio'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO configuracoes (chave, valor) VALUES ('nome_torneio', 'Torneio Pro')")

    # Tabela de Utilizadores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            papel TEXT DEFAULT 'aluno',
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (username, senha, papel) VALUES ('admin', 'admin123', 'admin')")

    # Tabela de Modalidades
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modalidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            limite_atletas INTEGER NOT NULL
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM modalidades")
    if cursor.fetchone()[0] == 0:
        mod_iniciais = [
            ("Futsal", 10),
            ("Voleibol", 8),
            ("Basquetebol", 8),
            ("Handebol", 10)
        ]
        cursor.executemany("INSERT INTO modalidades (nome, limite_atletas) VALUES (?, ?)", mod_iniciais)

    # Tabela de Equipas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            modalidade TEXT DEFAULT 'Futsal',
            pontos INTEGER DEFAULT 0,
            jogos INTEGER DEFAULT 0,
            vitorias INTEGER DEFAULT 0,
            empates INTEGER DEFAULT 0,
            derrotas INTEGER DEFAULT 0,
            gols_pro INTEGER DEFAULT 0,
            gols_contra INTEGER DEFAULT 0,
            saldo_gols INTEGER DEFAULT 0,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabela de Confrontos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS confrontos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modalidade TEXT NOT NULL,
            time1 TEXT NOT NULL,
            time2 TEXT NOT NULL,
            gols1 INTEGER DEFAULT 0,
            gols2 INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pendente'
        )
    """)

    # Tabela de Mensagens do Mural
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            autor TEXT NOT NULL,
            categoria TEXT DEFAULT 'Avisos Gerais',
            conteudo TEXT NOT NULL,
            data TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    verificar_e_limpar_dados_90_dias()

def obter_nome_torneio_db():
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracoes WHERE chave = 'nome_torneio'")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else "Torneio Pro"

def atualizar_nome_torneio_db(novo_nome):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE configuracoes SET valor = ? WHERE chave = 'nome_torneio'", (novo_nome,))
    conn.commit()
    conn.close()

def verificar_e_limpar_dados_90_dias():
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    limite_data = datetime.now() - timedelta(days=90)
    limite_str = limite_data.strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("DELETE FROM usuarios WHERE papel != 'admin' AND data_criacao < ?", (limite_str,))
        cursor.execute("DELETE FROM times WHERE data_criacao < ?", (limite_str,))
        cursor.execute("DELETE FROM mensagens WHERE data < ?", (limite_str,))
        cursor.execute("DELETE FROM confrontos")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()

def registar_usuario(username, senha):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (username, senha, papel, data_criacao) VALUES (?, ?, 'aluno', ?)", 
                       (username, senha, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return True, "Registo efetuado com sucesso!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Erro: Este nome de utilizador já está a ser utilizado."

def verificar_login(username, senha):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT papel FROM usuarios WHERE username = ? AND senha = ?", (username, senha))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def carregar_usuarios_db():
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, senha, papel FROM usuarios")
    dados = cursor.fetchall()
    conn.close()
    return dados

def resetar_senha_db(user_id, nova_senha):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (nova_senha, user_id))
    conn.commit()
    conn.close()

def alterar_papel_db(user_id, novo_papel):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET papel = ? WHERE id = ?", (novo_papel, user_id))
    conn.commit()
    conn.close()

def apagar_usuario_db(user_id):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ? AND username != 'admin'", (user_id,))
    conn.commit()
    conn.close()

def carregar_modalidades_db():
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, limite_atletas FROM modalidades")
    dados = cursor.fetchall()
    conn.close()
    return dados

def atualizar_limite_modalidade_db(mod_id, novo_limite):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE modalidades SET limite_atletas = ? WHERE id = ?", (novo_limite, mod_id))
    conn.commit()
    conn.close()

def adicionar_modalidade_db(nome, limite):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO modalidades (nome, limite_atletas) VALUES (?, ?)", (nome, limite))
        conn.commit()
        conn.close()
        return True, "Modalidade adicionada com sucesso!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Erro: Esta modalidade já existe."

def apagar_modalidade_db(mod_id):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM modalidades WHERE id = ?", (mod_id,))
    conn.commit()
    conn.close()

def adicionar_time_db(nome, modalidade):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO times (nome, modalidade, data_criacao) VALUES (?, ?, ?)", 
                       (nome, modalidade, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        return True, "Equipa registada com sucesso!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Erro: Esta equipa já se encontra registada no torneio!"

def carregar_times_db():
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nome, modalidade, pontos, jogos, vitorias, empates, derrotas, gols_pro, gols_contra, saldo_gols FROM times ORDER BY pontos DESC, saldo_gols DESC")
    dados = cursor.fetchall()
    conn.close()
    return dados

def apagar_time_db(nome_time):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM times WHERE nome = ?", (nome_time,))
    conn.commit()
    conn.close()

def gerar_confrontos_automaticos():
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM confrontos")
    
    cursor.execute("SELECT DISTINCT modalidade FROM times")
    modalidades = cursor.fetchall()
    
    gerados = 0
    for mod in modalidades:
        m_nome = mod[0]
        cursor.execute("SELECT nome FROM times WHERE modalidade = ?", (m_nome,))
        times = [t[0] for t in cursor.fetchall()]
        
        for i in range(0, len(times) - 1, 2):
            cursor.execute("INSERT INTO confrontos (modalidade, time1, time2, status) VALUES (?, ?, ?, 'Pendente')", 
                           (m_nome, times[i], times[i+1]))
            gerados += 1
            
    conn.commit()
    conn.close()
    return gerados > 0, "Confrontos e chaveamento gerados com sucesso!"

def carregar_confrontos_db():
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, modalidade, time1, time2, gols1, gols2, status FROM confrontos")
    dados = cursor.fetchall()
    conn.close()
    return dados

def atualizar_resultado_confronto(conf_id, g1, g2):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    status = "Finalizado"
    cursor.execute("UPDATE confrontos SET gols1 = ?, gols2 = ?, status = ? WHERE id = ?", (g1, g2, status, conf_id))
    conn.commit()
    conn.close()

def publicar_mensagem_db(autor, categoria, conteudo):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mensagens (autor, categoria, conteudo, data) VALUES (?, ?, ?, ?)", 
                   (autor, categoria, conteudo, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def carregar_mensagens_db():
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, autor, categoria, conteudo FROM mensagens ORDER BY id DESC")
    dados = cursor.fetchall()
    conn.close()
    return dados

def apagar_mensagem_db(msg_id):
    conn = sqlite3.connect("torneio.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mensagens WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()