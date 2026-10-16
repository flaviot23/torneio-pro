import sqlite3
import random
import string

def gerar_codigo_torneio():
    letras = ''.join(random.choices(string.ascii_uppercase, k=3))
    numeros = ''.join(random.choices(string.digits, k=4))
    return f"TRN-{letras}{numeros}"

def init_db():
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS torneios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            codigo TEXT UNIQUE NOT NULL,
            criador TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            papel TEXT DEFAULT 'usuario'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens_recuperacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            torneio_id INTEGER,
            chave TEXT,
            valor TEXT,
            FOREIGN KEY (torneio_id) REFERENCES torneios (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modalidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            torneio_id INTEGER,
            nome TEXT,
            limite INTEGER,
            limite_por_equipe INTEGER DEFAULT 5,
            FOREIGN KEY (torneio_id) REFERENCES torneios (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS series_turmas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            torneio_id INTEGER,
            serie TEXT,
            turma TEXT,
            FOREIGN KEY (torneio_id) REFERENCES torneios (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS times (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            torneio_id INTEGER,
            nome TEXT,
            modalidade TEXT,
            serie TEXT,
            turma TEXT,
            logo_url TEXT,
            pontos INTEGER DEFAULT 0,
            jogos INTEGER DEFAULT 0,
            vitorias INTEGER DEFAULT 0,
            empates INTEGER DEFAULT 0,
            derrotas INTEGER DEFAULT 0,
            gols_pro INTEGER DEFAULT 0,
            gols_contra INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Ativa',
            FOREIGN KEY (torneio_id) REFERENCES torneios (id),
            UNIQUE(torneio_id, modalidade, nome)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participantes_equipa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time_id INTEGER,
            nome_aluno TEXT,
            funcao TEXT,
            FOREIGN KEY (time_id) REFERENCES times (id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS confrontos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            torneio_id INTEGER,
            modalidade TEXT,
            time1 TEXT,
            time2 TEXT,
            gols1 INTEGER DEFAULT 0,
            gols2 INTEGER DEFAULT 0,
            data_hora TEXT DEFAULT 'A definir',
            local TEXT DEFAULT 'Quadra Principal',
            status TEXT DEFAULT 'Pendente',
            FOREIGN KEY (torneio_id) REFERENCES torneios (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            torneio_id INTEGER,
            autor TEXT,
            categoria TEXT,
            conteudo TEXT,
            FOREIGN KEY (torneio_id) REFERENCES torneios (id)
        )
    """)

    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (username, email, senha, papel) VALUES (?, ?, ?, ?)",
                       ("admin", "admin@torneiosauto.com", "admin123", "admin"))
        conn.commit()

    conn.close()

def carregar_torneios_db():
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, codigo, criador FROM torneios")
    res = cursor.fetchall()
    conn.close()
    return res

def criar_torneio_db(nome, criador):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    codigo = gerar_codigo_torneio()
    try:
        cursor.execute("INSERT INTO torneios (nome, codigo, criador) VALUES (?, ?, ?)", (nome, codigo, criador))
        t_id = cursor.lastrowid
        cursor.execute("INSERT INTO configuracoes (torneio_id, chave, valor) VALUES (?, 'pontos_vitoria', '3')", (t_id,))
        cursor.execute("INSERT INTO configuracoes (torneio_id, chave, valor) VALUES (?, 'pontos_empate', '1')", (t_id,))
        conn.commit()
        conn.close()
        return True, codigo
    except Exception as e:
        conn.close()
        return False, str(e)

def apagar_torneio_db(torneio_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM times WHERE torneio_id = ?", (torneio_id,))
    times = cursor.fetchall()
    for t in times:
        cursor.execute("DELETE FROM participantes_equipa WHERE time_id = ?", (t[0],))
    cursor.execute("DELETE FROM times WHERE torneio_id = ?", (torneio_id,))
    cursor.execute("DELETE FROM confrontos WHERE torneio_id = ?", (torneio_id,))
    cursor.execute("DELETE FROM modalidades WHERE torneio_id = ?", (torneio_id,))
    cursor.execute("DELETE FROM series_turmas WHERE torneio_id = ?", (torneio_id,))
    cursor.execute("DELETE FROM mensagens WHERE torneio_id = ?", (torneio_id,))
    cursor.execute("DELETE FROM configuracoes WHERE torneio_id = ?", (torneio_id,))
    cursor.execute("DELETE FROM torneios WHERE id = ?", (torneio_id,))
    conn.commit()
    conn.close()

def atualizar_nome_torneio_db(torneio_id, novo_nome):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE torneios SET nome = ? WHERE id = ?", (novo_nome, torneio_id))
    conn.commit()
    conn.close()

def obter_configuracao_db(torneio_id, chave):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracoes WHERE torneio_id = ? AND chave = ?", (torneio_id, chave))
    res = cursor.fetchone()
    conn.close()
    return int(res[0]) if res else (3 if chave == 'pontos_vitoria' else 1)

def atualizar_configuracao_db(torneio_id, chave, valor):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM configuracoes WHERE torneio_id = ? AND chave = ?", (torneio_id, chave))
    if cursor.fetchone():
        cursor.execute("UPDATE configuracoes SET valor = ? WHERE torneio_id = ? AND chave = ?", (valor, torneio_id, chave))
    else:
        cursor.execute("INSERT INTO configuracoes (torneio_id, chave, valor) VALUES (?, ?, ?)", (torneio_id, chave, valor))
    conn.commit()
    conn.close()

def registar_usuario(username, email, senha):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (username, email, senha, papel) VALUES (?, ?, ?, 'usuario')", 
                       (username, email, senha))
        conn.commit()
        conn.close()
        return True, "Sucesso"
    except Exception as e:
        conn.close()
        return False, "Nome de utilizador ou e-mail já registados."

def verificar_login(username_ou_email, senha):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT papel FROM usuarios WHERE (username = ? OR email = ?) AND senha = ?", 
                   (username_ou_email, username_ou_email, senha))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def carregar_usuarios_db():
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, senha, papel FROM usuarios")
    res = cursor.fetchall()
    conn.close()
    return res

def contar_usuarios_db():
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    res = cursor.fetchone()[0]
    conn.close()
    return res

def alterar_papel_db(user_id, novo_papel):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET papel = ? WHERE id = ?", (novo_papel, user_id))
    conn.commit()
    conn.close()

def apagar_usuario_db(user_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ? AND username != 'admin'", (user_id,))
    conn.commit()
    conn.close()

def resetar_senha_db(username, nova_senha):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET senha = ? WHERE username = ?", (nova_senha, username))
    conn.commit()
    conn.close()

def criar_token_recuperacao(email, token):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM usuarios WHERE email = ?", (email,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return False, "E-mail não encontrado"
    username = res[0]
    cursor.execute("INSERT INTO tokens_recuperacao (username, token) VALUES (?, ?)", (username, token))
    conn.commit()
    conn.close()
    return True, username

def verificar_token_db(token):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM tokens_recuperacao WHERE token = ?", (token,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def carregar_modalidades_db(torneio_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, limite, limite_por_equipe FROM modalidades WHERE torneio_id = ?", (torneio_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def adicionar_modalidade_db(torneio_id, nome, limite, limite_por_equipe):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO modalidades (torneio_id, nome, limite, limite_por_equipe) VALUES (?, ?, ?, ?)", (torneio_id, nome, limite, limite_por_equipe))
    conn.commit()
    conn.close()

def apagar_modalidade_db(mod_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM modalidades WHERE id = ?", (mod_id,))
    conn.commit()
    conn.close()

def carregar_series_turmas_db(torneio_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, serie, turma FROM series_turmas WHERE torneio_id = ?", (torneio_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def adicionar_serie_turma_db(torneio_id, serie, turma):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO series_turmas (torneio_id, serie, turma) VALUES (?, ?, ?)", (torneio_id, serie, turma))
    conn.commit()
    conn.close()

def apagar_serie_turma_db(st_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM series_turmas WHERE id = ?", (st_id,))
    conn.commit()
    conn.close()

def adicionar_time_db(torneio_id, nome, modalidade, serie, turma, logo_url, participantes_titulares, participantes_reservas):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM times WHERE torneio_id = ? AND modalidade = ? AND LOWER(nome) = LOWER(?)", (torneio_id, modalidade, nome))
        if cursor.fetchone():
            conn.close()
            return False, f"A equipa '{nome}' já se encontra registada nesta modalidade!"

        cursor.execute("""
            INSERT INTO times (torneio_id, nome, modalidade, serie, turma, logo_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (torneio_id, nome, modalidade, serie, turma, logo_url))
        time_id = cursor.lastrowid
        
        for aluno in participantes_titulares:
            if aluno.strip():
                cursor.execute("INSERT INTO participantes_equipa (time_id, nome_aluno, funcao) VALUES (?, ?, 'Titular')", (time_id, aluno.strip()))
                
        for aluno in participantes_reservas:
            if aluno.strip():
                cursor.execute("INSERT INTO participantes_equipa (time_id, nome_aluno, funcao) VALUES (?, ?, 'Reserva')", (time_id, aluno.strip()))
                
        conn.commit()
        conn.close()
        return True, "Sucesso"
    except Exception as e:
        conn.close()
        return False, f"Erro ao criar equipa: {str(e)}"

def carregar_times_db(torneio_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, modalidade, serie, turma, logo_url, pontos, jogos, vitorias, empates, derrotas, gols_pro, gols_contra, (gols_pro - gols_contra), status 
        FROM times WHERE torneio_id = ? ORDER BY pontos DESC, (gols_pro - gols_contra) DESC, gols_pro DESC
    """, (torneio_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def carregar_participantes_time(time_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nome_aluno, funcao FROM participantes_equipa WHERE time_id = ?", (time_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def contar_times_db(torneio_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM times WHERE torneio_id = ?", (torneio_id,))
    res = cursor.fetchone()[0]
    conn.close()
    return res

def apagar_time_db(time_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM participantes_equipa WHERE time_id = ?", (time_id,))
    cursor.execute("DELETE FROM times WHERE id = ?", (time_id,))
    conn.commit()
    conn.close()

def gerar_confrontos_automaticos(torneio_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM confrontos WHERE torneio_id = ?", (torneio_id,))
    
    cursor.execute("SELECT DISTINCT modalidade FROM times WHERE torneio_id = ?", (torneio_id,))
    mods = cursor.fetchall()
    
    for m in mods:
        mod_nome = m[0]
        cursor.execute("SELECT nome FROM times WHERE torneio_id = ? AND modalidade = ?", (torneio_id, mod_nome))
        times = [t[0] for t in cursor.fetchall()]
        
        if len(times) == 1:
            # Regra de W.O. automática caso exista apenas 1 equipa na modalidade
            cursor.execute("""
                INSERT INTO confrontos (torneio_id, modalidade, time1, time2, data_hora, local, status, gols1, gols2)
                VALUES (?, ?, ?, 'SEM ADVERSÁRIO (W.O.)', 'W.O.', 'W.O.', 'Finalizado', 3, 0)
            """, (torneio_id, mod_nome, times[0]))
        else:
            for i in range(len(times)):
                for j in range(i + 1, len(times)):
                    cursor.execute("""
                        INSERT INTO confrontos (torneio_id, modalidade, time1, time2, data_hora, local, status)
                        VALUES (?, ?, ?, ?, 'A definir', 'Quadra Principal', 'Pendente')
                    """, (torneio_id, mod_nome, times[i], times[j]))
    conn.commit()
    conn.close()

def carregar_confrontos_db(torneio_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, modalidade, time1, time2, gols1, gols2, data_hora, local, status FROM confrontos WHERE torneio_id = ?", (torneio_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def atualizar_resultado_confronto(conf_id, gols1, gols2, data_hora, local, status_opcao):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT torneio_id, modalidade, time1, time2 FROM confrontos WHERE id = ?", (conf_id,))
    conf = cursor.fetchone()
    if not conf:
        conn.close()
        return
    
    t_id, mod, t1, t2 = conf[0], conf[1], conf[2], conf[3]
    p_vitoria = obter_configuracao_db(t_id, 'pontos_vitoria')
    p_empate = obter_configuracao_db(t_id, 'pontos_empate')
    
    cursor.execute("UPDATE confrontos SET gols1 = ?, gols2 = ?, data_hora = ?, local = ?, status = ? WHERE id = ?", 
                   (gols1, gols2, data_hora, local, status_opcao, conf_id))
    
    # Resetar pontuações da modalidade afetada antes de recalcular
    cursor.execute("SELECT DISTINCT nome FROM times WHERE torneio_id = ? AND modalidade = ?", (t_id, mod))
    times_mod = [tm[0] for tm in cursor.fetchall()]
    for time_nome in times_mod:
        cursor.execute("""
            UPDATE times SET pontos = 0, jogos = 0, vitorias = 0, empates = 0, derrotas = 0, gols_pro = 0, gols_contra = 0 
            WHERE torneio_id = ? AND modalidade = ? AND nome = ?
        """, (t_id, mod, time_nome))
        
    cursor.execute("SELECT id, time1, time2, gols1, gols2, status FROM confrontos WHERE torneio_id = ? AND modalidade = ? AND status != 'Pendente'", (t_id, mod))
    confs_validos = cursor.fetchall()
    
    for cv in confs_validos:
        c_id, c_t1, c_t2, c_g1, c_g2, c_stat = cv
        if c_stat == 'Finalizado':
            if c_t2 == 'SEM ADVERSÁRIO (W.O.)':
                # Processar vitória por W.O. automático
                cursor.execute("UPDATE times SET jogos = jogos + 1, vitorias = vitorias + 1, pontos = pontos + ?, gols_pro = gols_pro + ?, gols_contra = gols_contra + ? WHERE torneio_id = ? AND modalidade = ? AND nome = ?", (p_vitoria, c_g1, c_g2, t_id, mod, c_t1))
            else:
                cursor.execute("UPDATE times SET jogos = jogos + 1, gols_pro = gols_pro + ?, gols_contra = gols_contra + ? WHERE torneio_id = ? AND nome = ?", (c_g1, c_g2, t_id, c_t1))
                cursor.execute("UPDATE times SET jogos = jogos + 1, gols_pro = gols_pro + ?, gols_contra = gols_contra + ? WHERE torneio_id = ? AND nome = ?", (c_g2, c_g1, t_id, c_t2))
                
                if c_g1 > c_g2:
                    cursor.execute("UPDATE times SET vitorias = vitorias + 1, pontos = pontos + ? WHERE torneio_id = ? AND nome = ?", (p_vitoria, t_id, c_t1))
                    cursor.execute("UPDATE times SET derrotas = derrotas + 1 WHERE torneio_id = ? AND nome = ?", (t_id, c_t2))
                elif c_g1 < c_g2:
                    cursor.execute("UPDATE times SET vitorias = vitorias + 1, pontos = pontos + ? WHERE torneio_id = ? AND nome = ?", (p_vitoria, t_id, c_t2))
                    cursor.execute("UPDATE times SET derrotas = derrotas + 1 WHERE torneio_id = ? AND nome = ?", (t_id, c_t1))
                else:
                    cursor.execute("UPDATE times SET empates = empates + 1, pontos = pontos + ? WHERE torneio_id = ? AND nome = ?", (p_empate, t_id, c_t1))
                    cursor.execute("UPDATE times SET empates = empates + 1, pontos = pontos + ? WHERE torneio_id = ? AND nome = ?", (p_empate, t_id, c_t2))
        elif c_stat == 'Desclassificar T1':
            cursor.execute("UPDATE times SET status = 'Desclassificada' WHERE torneio_id = ? AND nome = ?", (t_id, c_t1))
        elif c_stat == 'Desclassificar T2':
            cursor.execute("UPDATE times SET status = 'Desclassificada' WHERE torneio_id = ? AND nome = ?", (t_id, c_t2))

    conn.commit()
    conn.close()

def publicar_mensagem_db(torneio_id, autor, categoria, conteudo):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mensagens (torneio_id, autor, categoria, conteudo) VALUES (?, ?, ?, ?)", (torneio_id, autor, categoria, conteudo))
    conn.commit()
    conn.close()

def carregar_mensagens_db(torneio_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, autor, categoria, conteudo FROM mensagens WHERE torneio_id = ?", (torneio_id,))
    res = cursor.fetchall()
    conn.close()
    return res

def apagar_mensagem_db(msg_id):
    conn = sqlite3.connect("torneio_vtd.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mensagens WHERE id = ?", (msg_id,))
    conn.commit()
    conn.close()