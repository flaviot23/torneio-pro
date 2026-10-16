import secrets
import resend
from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from database import (
    init_db, carregar_torneios_db, criar_torneio_db, apagar_torneio_db, obter_configuracao_db, atualizar_configuracao_db, atualizar_nome_torneio_db,
    registar_usuario, verificar_login, carregar_usuarios_db, contar_usuarios_db,
    resetar_senha_db, criar_token_recuperacao, verificar_token_db, alterar_papel_db, apagar_usuario_db,
    carregar_modalidades_db, adicionar_modalidade_db, apagar_modalidade_db, 
    carregar_series_turmas_db, adicionar_serie_turma_db, apagar_serie_turma_db,
    adicionar_time_db, carregar_times_db, carregar_participantes_time, contar_times_db, apagar_time_db, 
    gerar_confrontos_automaticos, carregar_confrontos_db, atualizar_resultado_confronto, 
    publicar_mensagem_db, carregar_mensagens_db, apagar_mensagem_db
)

app = FastAPI()

RESEND_API_KEY = "re_Bm1Rc8Wp_73MtCmEhiSyzCg7yF6vuGbWG"
resend.api_key = RESEND_API_KEY

try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    pass

init_db()

def enviar_email_real(destinatario, link_recuperacao):
    if not RESEND_API_KEY.startswith("re_"):
        return False
    try:
        resend.Emails.send({
            "from": "Torneios Auto <onboarding@resend.dev>",
            "to": destinatario,
            "subject": "Recuperação de Senha - Torneios Auto",
            "html": f"""
            <div style="font-family: sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; border-radius: 8px; max-width: 500px; margin: 0 auto;">
                <h2 style="color: #f0f6fc; text-align: center;">🏆 Torneios Auto</h2>
                <p>Recebemos um pedido para redefinir a palavra-passe da sua conta.</p>
                <p style="text-align: center; margin: 25px 0;">
                    <a href="{link_recuperacao}" style="background: #238636; color: white; padding: 12px 20px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Redefinir Minha Senha</a>
                </p>
            </div>
            """
        })
        return True
    except Exception as e:
        print(f"\n[ERRO AO ENVIAR E-MAIL]: {e}\n")
        return False

def resposta_html_sem_cache(html_content: str):
    response = HTMLResponse(content=html_content)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/login", response_class=HTMLResponse)
def pagina_login(erro: str = None):
    aviso = f"<p style='color: #da3633; margin-bottom: 15px; text-align: center; font-size: 14px;'>{erro}</p>" if erro else ""
    html = f"""
    <!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><title>Login - Torneios Auto</title>
    <style>body {{ background: #0d1117; color: #c9d1d9; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
    .card {{ background: #161b22; padding: 30px; border-radius: 12px; border: 1px solid #30363d; width: 320px; }}
    input {{ width: 100%; padding: 10px; margin-bottom: 15px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; box-sizing: border-box; }}
    button {{ width: 100%; padding: 10px; background: #238636; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }}</style>
    </head><body><div class="card"><h2 style="text-align:center; color:#f0f6fc;">🏆 Torneios Auto</h2>{aviso}
    <form action="/login" method="post">
        <input type="text" name="username" placeholder="Utilizador ou E-mail" required>
        <input type="password" name="senha" placeholder="Palavra-passe" required>
        <button type="submit">Entrar</button>
    </form>
    <div style="text-align:center; margin-top:15px; font-size:13px;"><p><a href="/registar" style="color:#58a6ff;">Registar-se</a> | <a href="/recuperar" style="color:#58a6ff;">Esqueceu-se da senha?</a></p></div>
    </div></body></html>
    """
    return resposta_html_sem_cache(html)

@app.post("/login")
def processar_login(username: str = Form(...), senha: str = Form(...)):
    papel = verificar_login(username.strip(), senha.strip())
    if papel:
        u_limpo = username.strip()
        torneios = carregar_torneios_db()
        meus_torneios = torneios if papel == 'admin' else [t for t in torneios if str(t[3]).lower() == u_limpo.lower()]
        url_destino = f"/t/{meus_torneios[0][2]}" if meus_torneios else "/"
        response = RedirectResponse(url=url_destino, status_code=303)
        response.set_cookie(key="user", value=u_limpo)
        return response
    return RedirectResponse(url="/login?erro=Utilizador+ou+palavra-passe+incorretos", status_code=303)

@app.get("/registar", response_class=HTMLResponse)
def pagina_registar(erro: str = None):
    aviso = f"<p style='color: #da3633; margin-bottom: 15px; text-align: center; font-size: 14px;'>{erro}</p>" if erro else ""
    html = f"""
    <!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><title>Registar - Torneios Auto</title>
    <style>
        body {{ background: #0d1117; color: #c9d1d9; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px 0; }}
        .card {{ background: #161b22; padding: 30px; border-radius: 12px; border: 1px solid #30363d; width: 380px; box-sizing: border-box; }}
        input {{ width: 100%; padding: 10px; margin-bottom: 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; box-sizing: border-box; }}
        button {{ width: 100%; padding: 10px; background: #238636; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }}
    </style>
    </head><body><div class="card"><h2 style="text-align:center; color:#f0f6fc; margin-top:0;">📝 Criar Conta</h2>{aviso}
    <form action="/registar" method="post">
        <input type="text" name="username" placeholder="Nome de Utilizador" required>
        <input type="email" name="email" placeholder="E-mail" required>
        <input type="password" name="senha" placeholder="Palavra-passe" required>
        <button type="submit">Criar Conta e Entrar</button>
    </form>
    <div style="text-align:center; margin-top:15px; font-size:13px;"><a href="/login" style="color:#58a6ff;">Já tem conta? Fazer Login</a></div>
    </div></body></html>
    """
    return resposta_html_sem_cache(html)

@app.post("/registar")
def processar_registar(username: str = Form(...), email: str = Form(...), senha: str = Form(...)):
    u_limpo, e_limpo, s_limpo = username.strip(), email.strip(), senha.strip()
    sucesso, msg = registar_usuario(u_limpo, e_limpo, s_limpo)
    if not sucesso:
        return RedirectResponse(url=f"/registar?erro={msg}", status_code=303)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="user", value=u_limpo)
    return response

@app.get("/recuperar", response_class=HTMLResponse)
def pagina_recuperar(msg: str = None):
    aviso = f"<p style='color: #3fb950; text-align: center; font-size: 13px;'>{msg}</p>" if msg else ""
    html = f"""
    <!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><title>Recuperar Senha</title>
    <style>body {{ background: #0d1117; color: #c9d1d9; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
    .card {{ background: #161b22; padding: 30px; border-radius: 12px; border: 1px solid #30363d; width: 350px; }}
    input {{ width: 100%; padding: 10px; margin-bottom: 15px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; box-sizing: border-box; }}
    button {{ width: 100%; padding: 10px; background: #8957e5; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }}</style>
    </head><body><div class="card"><h2 style="text-align:center; color:#f0f6fc;">🔑 Recuperar Senha</h2>{aviso}
    <form action="/recuperar" method="post"><input type="email" name="email" placeholder="O seu e-mail" required><button type="submit">Enviar E-mail</button></form>
    <div style="text-align:center; margin-top:15px;"><a href="/login" style="color:#58a6ff; font-size:13px;">Voltar ao Login</a></div>
    </div></body></html>
    """
    return resposta_html_sem_cache(html)

@app.post("/recuperar")
def processar_recuperar(request: Request, email: str = Form(...)):
    token = secrets.token_urlsafe(32)
    sucesso, _ = criar_token_recuperacao(email.strip(), token)
    if sucesso:
        enviar_email_real(email.strip(), f"{request.base_url}resetar/{token}")
    return RedirectResponse(url="/recuperar?msg=Instruções enviadas para o e-mail.", status_code=303)

@app.get("/resetar/{token}", response_class=HTMLResponse)
def pagina_resetar(token: str):
    username = verificar_token_db(token)
    if not username:
        return resposta_html_sem_cache("<body style='background:#0d1117; color:white; text-align:center; padding-top:20vh;'><h3>⚠️ Link inválido ou expirado.</h3></body>")
    html = f"""
    <!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><title>Nova Senha</title>
    <style>body {{ background: #0d1117; color: #c9d1d9; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
    .card {{ background: #161b22; padding: 30px; border-radius: 12px; border: 1px solid #30363d; width: 320px; }}
    input {{ width: 100%; padding: 10px; margin-bottom: 15px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; box-sizing: border-box; }}
    button {{ width: 100%; padding: 10px; background: #238636; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }}</style>
    </head><body><div class="card"><h2 style="color:white; text-align:center;">Nova Senha</h2>
    <form action="/resetar/{token}" method="post"><input type="password" name="nova_senha" placeholder="Nova palavra-passe" required><button type="submit">Atualizar</button></form></div></body></html>
    """
    return resposta_html_sem_cache(html)

@app.post("/resetar/{token}")
def processar_resetar(token: str, nova_senha: str = Form(...)):
    username = verificar_token_db(token)
    if username:
        resetar_senha_db(username, nova_senha)
    return RedirectResponse(url="/login", status_code=303)

@app.get("/", response_class=HTMLResponse)
def pagina_inicio_geral(request: Request, erro: str = None):
    username = request.cookies.get("user")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    torneios = carregar_torneios_db()
    papel = next((u[4] for u in carregar_usuarios_db() if u[1] == username), "usuario")
    torneios_visiveis = torneios if papel == 'admin' else [t for t in torneios if str(t[3]).lower() == username.lower()]

    if torneios_visiveis:
        return RedirectResponse(url=f"/t/{torneios_visiveis[0][2]}", status_code=303)

    aviso_erro = f"<p style='color: #da3633; font-size: 13px;'>{erro}</p>" if erro else ""

    html = f"""
    <!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><title>Boas-Vindas</title>
    <style>body {{ background: #0d1117; color: #c9d1d9; font-family: sans-serif; margin: 0; padding: 20px; }}
    .container {{ max-width: 800px; margin: 50px auto; background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 25px; text-align: center; }}
    input {{ width: 100%; padding: 10px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: white; box-sizing: border-box; margin-bottom: 10px; }}
    button {{ background: #238636; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; width:100%; }}</style>
    </head><body><div class="container">
        <h2>🏆 Bem-vindo ao Torneios Auto, {username}</h2>
        <p>Ainda não tens nenhum torneio criado nem integrado.</p>
        {aviso_erro}
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; margin-top:20px;">
            <div style="background:#0d1117; padding:15px; border-radius:8px; border:1px solid #30363d;">
                <h4>Criar Novo Torneio</h4>
                <form action="/criar-torneio" method="post">
                    <input type="text" name="nome_novo_torneio" placeholder="Nome do Torneio" required>
                    <button type="submit">Criar</button>
                </form>
            </div>
            <div style="background:#0d1117; padding:15px; border-radius:8px; border:1px solid #30363d;">
                <h4>Entrar por Código</h4>
                <form action="/entrar-codigo" method="post">
                    <input type="text" name="codigo_torneio" placeholder="Ex: TRN-ABC1234" required>
                    <button type="submit" style="background:#1f6beb;">Aceder</button>
                </form>
            </div>
        </div>
    </div></body></html>
    """
    return resposta_html_sem_cache(html)

@app.post("/entrar-codigo")
def entrar_com_codigo(codigo_torneio: str = Form(...)):
    codigo_limpo = codigo_torneio.strip().upper()
    torneios = carregar_torneios_db()
    t_encontrado = next((t for t in torneios if t[2].upper() == codigo_limpo), None)
    if t_encontrado:
        return RedirectResponse(url=f"/t/{t_encontrado[2]}", status_code=303)
    return RedirectResponse(url="/?erro=Código+de+torneio+não+encontrado", status_code=303)

@app.get("/t/{codigo_torneio}", response_class=HTMLResponse)
def index_torneio(request: Request, codigo_torneio: str, tab: str = "painel", erro_inscricao: str = None, mod_sel: str = None):
    username = request.cookies.get("user")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    torneios = carregar_torneios_db()
    t_atual = next((t for t in torneios if t[2].upper() == codigo_torneio.upper()), None)
    if not t_atual:
        return RedirectResponse(url="/", status_code=303)
    
    t_id, nome_torneio, codigo_exibicao, criador_torneio = t_atual[0], t_atual[1], t_atual[2], t_atual[3]
    papel_global = next((u[4] for u in carregar_usuarios_db() if u[1] == username), "usuario")
    pode_gerir_torneio = (papel_global == 'admin') or (username.lower() == str(criador_torneio).lower())
    torneios_visiveis_select = torneios if papel_global == 'admin' else [t for t in torneios if str(t[3]).lower() == username.lower()]

    modalidades = carregar_modalidades_db(t_id)
    series_turmas = carregar_series_turmas_db(t_id)
    times = carregar_times_db(t_id)
    confrontos = carregar_confrontos_db(t_id)
    mensagens = carregar_mensagens_db(t_id)

    modalidade_atual_nome = mod_sel if mod_sel else (modalidades[0][1] if modalidades else "")
    mod_obj = next((m for m in modalidades if m[1] == modalidade_atual_nome), None)
    
    n_titulares = mod_obj[2] if mod_obj else 5
    n_reservas = mod_obj[3] if mod_obj else 3

    opcoes_modalidades = "".join([f"<option value='{m[1]}' {'selected' if m[1]==modalidade_atual_nome else ''}>{m[1]} (Titulares: {m[2]}, Reservas: {m[3]})</option>" for m in modalidades])
    opcoes_series = "".join([f"<option value='{st[1]} - Turma {st[2]}'>{st[1]} (Turma {st[2]})</option>" for st in series_turmas])
    if not opcoes_series:
        opcoes_series = "<option value='3º - Turma A'>3º (Turma A)</option>"

    opcoes_torneios_select = "".join([f"<option value='{t[2]}' {'selected' if t[2].upper()==codigo_torneio.upper() else ''}>{t[1]} ({t[2]})</option>" for t in torneios_visiveis_select])
    erro_box = f"<div style='background:#da3633; color:white; padding:10px; border-radius:6px; margin-bottom:15px; font-size:13px;'>⚠️ {erro_inscricao}</div>" if erro_inscricao else ""

    linhas_tabela = ""
    for t in times:
        participantes = carregar_participantes_time(t[0])
        titulares_lista = [p[0] for p in participantes if p[1] == 'Titular']
        reservas_lista = [p[0] for p in participantes if p[1] == 'Reserva']
        
        titulares_str = ", ".join(titulares_lista) if titulares_lista else "-"
        reservas_str = ", ".join(reservas_lista) if reservas_lista else "-"
        
        botao_apagar = f"""<form action="/t/{codigo_exibicao}/apagar-time" method="post" style="display:inline;"><input type="hidden" name="time_id" value="{t[0]}"><button type="submit" style="background: #da3633; color:white; border:none; padding:4px 8px; border-radius:4px; cursor:pointer; font-size:11px;">Apagar</button></form>""" if pode_gerir_torneio else ""
        status_tag = f" <span style='background:#da3633; color:white; padding:1px 5px; border-radius:3px; font-size:10px;'>DESCLASSIFICADA</span>" if t[14] == 'Desclassificada' else ""
        
        linhas_tabela += f"""
            <tr style="border-bottom: 1px solid #21262d;">
                <td style="padding: 12px; color: #f0f6fc; font-weight: 600;">{t[1]} <span style="font-size: 11px; color: #8b949e;">({t[3]} - {t[4]})</span>{status_tag}
                    <div style="font-size: 11px; color: #3fb950; margin-top:4px;">⭐ <b>Titulares:</b> {titulares_str}</div>
                    <div style="font-size: 11px; color: #58a6ff; margin-top:2px;">🔄 <b>Reservas:</b> {reservas_str}</div>
                </td>
                <td style="padding: 12px;"><span style="background: #1f6beb; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{t[2]}</span></td>
                <td style="padding: 12px; text-align: center; color: #3fb950; font-weight: 700;">{t[6]}</td>
                <td style="padding: 12px; text-align: center; color: #c9d1d9;">{t[7]}</td>
                <td style="padding: 12px; text-align: center;">{botao_apagar}</td>
            </tr>
        """

    lista_avisos_html = ""
    for m in mensagens:
        btn_del = f"""<form action="/t/{codigo_exibicao}/apagar-mensagem" method="post" style="display:inline;"><input type="hidden" name="msg_id" value="{m[0]}"><button type="submit" style="background:none; border:none; color:#da3633; cursor:pointer; font-size:11px;">Excluir</button></form>""" if pode_gerir_torneio else ""
        lista_avisos_html += f"""
            <div style="background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 10px; margin-bottom: 8px; font-size: 13px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="background: #1f6beb; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold;">{m[2]}</span>
                    <div><span style="color: #8b949e; font-size: 11px;">Por: {m[1]}</span> {btn_del}</div>
                </div>
                <div style="color: #f0f6fc;">{m[3]}</div>
            </div>
        """

    campos_titulares = "".join([f"<input type='text' name='titular_{i}' placeholder='Titular {i}' required style='margin-bottom:6px;'>" for i in range(1, n_titulares + 1)])
    campos_reservas = "".join([f"<input type='text' name='reserva_{j}' placeholder='Reserva {j}' style='margin-bottom:6px;'>" for j in range(1, n_reservas + 1)]) if n_reservas > 0 else "<p style='color:#8b949e; font-size:12px;'>Sem reservas para esta modalidade.</p>"

    mods_rows = "".join([f"<div style='display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid #21262d; font-size:12px;'><span>{m[1]} (Titulares: {m[2]}, Reservas: {m[3]})</span><form action='/t/{codigo_exibicao}/apagar-modalidade' method='post'><input type='hidden' name='mod_id' value='{m[0]}'><button style='background:#da3633; color:white; border:none; font-size:10px;'>X</button></form></div>" for m in modalidades])
    series_rows = "".join([f"<div style='display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid #21262d; font-size:12px;'><span>{st[1]} (Turma {st[2]})</span><form action='/t/{codigo_exibicao}/apagar-serie-turma' method='post'><input type='hidden' name='st_id' value='{st[0]}'><button style='background:#da3633; color:white; border:none; font-size:10px;'>X</button></form></div>" for st in series_turmas])

    botao_apagar_torneio = f"""
    <form action="/t/{codigo_exibicao}/apagar-torneio" method="post" onsubmit="return confirm('Tens a certeza absoluta que pretendes apagar este campeonato por completo?');" style="margin:0;">
        <button type="submit" style="background:#da3633; color:white; border:none; padding:6px 12px; border-radius:6px; font-weight:bold; cursor:pointer; font-size:12px;">🗑️ Apagar Torneio</button>
    </form>
    """ if pode_gerir_torneio else ""

    painel_admin_html = ""
    if pode_gerir_torneio:
        painel_admin_html = f"""
        <div style="background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 25px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="color: #f0f6fc; margin: 0;">🛡️ Configurar Modalidades e Vagas</h3>
                {botao_apagar_torneio}
            </div>
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                <div>
                    <h4 style="color: #8b949e; font-size: 13px;">Adicionar Nova Modalidade com Vagas Específicas</h4>
                    <form action="/t/{codigo_exibicao}/adicionar-modalidade" method="post" style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 8px; align-items: flex-end;">
                        <div><label style="font-size:11px; color:#8b949e;">Nome:</label><input type="text" name="nome_mod" placeholder="Ex: Futsal" required style="padding:6px;"></div>
                        <div><label style="font-size:11px; color:#8b949e;">Titulares:</label><input type="number" name="titulares" value="5" min="1" required style="padding:6px;"></div>
                        <div><label style="font-size:11px; color:#8b949e;">Reservas:</label><input type="number" name="reservas" value="3" min="0" required style="padding:6px;"></div>
                        <div><button type="submit" style="background:#238636; color:white; border:none; padding:8px; border-radius:6px; font-weight:bold; cursor:pointer;">Criar</button></div>
                    </form>
                    <div style="max-height: 120px; overflow-y: auto; margin-top: 10px;">{mods_rows}</div>
                </div>
                <div>
                    <h4 style="color: #8b949e; font-size: 13px;">Séries/Turmas</h4>
                    <form action="/t/{codigo_exibicao}/adicionar-serie-turma" method="post" style="display: flex; gap: 4px; margin-bottom: 6px;">
                        <input type="text" name="nome_serie" placeholder="Série" required style="flex:2; padding:6px; font-size:11px;">
                        <input type="text" name="letra" placeholder="A" required style="flex:1; padding:6px; font-size:11px;">
                        <button type="submit" style="background:#238636; color:white; border:none; padding:6px; font-size:11px;">+</button>
                    </form>
                    <div style="max-height: 100px; overflow-y: auto;">{series_rows}</div>
                </div>
            </div>
        </div>
        """

    html = f"""
    <!DOCTYPE html><html lang="pt"><head><meta charset="UTF-8"><title>{nome_torneio}</title>
    <style>
        body {{ background: #0d1117; color: #c9d1d9; font-family: sans-serif; margin: 0; padding: 20px; }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        .header, .multi-bar, .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
        .nav-tabs {{ display: flex; gap: 10px; margin-bottom: 20px; }}
        .tab-btn {{ background: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 10px 20px; border-radius: 8px; font-weight: 600; text-decoration: none; }}
        .tab-btn.active {{ background: #238636; color: white; }}
        input, select, textarea {{ width: 100%; padding: 8px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; box-sizing: border-box; margin-bottom: 10px; }}
        .btn-green {{ background: #238636; color: white; border: none; padding: 10px; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%; }}
    </style>
    <script>
        function mudarTorneio(select) {{ if(select.value) window.location.href = '/t/' + select.value + '?tab={tab}'; }}
        function mudarModalidadeForm(select) {{
            window.location.href = '/t/{codigo_exibicao}?tab=painel&mod_sel=' + encodeURIComponent(select.value);
        }}
    </script>
    </head><body>
        <div class="container">
            <div class="header" style="display:flex; justify-content:space-between; align-items:center;">
                <div><h1 style="margin:0; color:white;">🏆 {nome_torneio}</h1><p style="margin:4px 0 0; font-size:12px; color:#8b949e;">Código: <b>{codigo_exibicao}</b></p></div>
                <div><span>{username}</span> | <a href="/logout" style="color:#da3633; font-weight:bold;">Sair</a></div>
            </div>

            <div class="multi-bar" style="display:flex; justify-content:space-between; align-items:center;">
                <select onchange="mudarTorneio(this)" style="width:260px; margin:0;">{opcoes_torneios_select}</select>
                <div style="display:flex; gap:10px; align-items:center;">
                    <form action="/entrar-codigo" method="post" style="display:flex; gap:6px; margin:0;">
                        <input type="text" name="codigo_torneio" placeholder="Código (Ex: TRN-ABC1234)" required style="width:170px; margin:0; padding:6px; font-size:11px;">
                        <button type="submit" style="background:#1f6beb; color:white; border:none; padding:6px 10px; border-radius:6px; font-weight:bold; cursor:pointer; font-size:11px;">Entrar</button>
                    </form>
                    <form action="/criar-torneio" method="post" style="display:flex; gap:6px; margin:0;">
                        <input type="text" name="nome_novo_torneio" placeholder="Novo Torneio" required style="width:140px; margin:0; padding:6px; font-size:11px;">
                        <button type="submit" style="background:#238636; color:white; border:none; padding:6px 10px; border-radius:6px; font-weight:bold; cursor:pointer; font-size:11px;">Criar</button>
                    </form>
                </div>
            </div>

            <div class="nav-tabs">
                <a href="/t/{codigo_exibicao}?tab=painel" class="tab-btn {'active' if tab=='painel' else ''}">📊 Painel & Inscrições</a>
                <a href="/t/{codigo_exibicao}?tab=confrontos" class="tab-btn {'active' if tab=='confrontos' else ''}">⚔️ Confrontos</a>
                <a href="/t/{codigo_exibicao}?tab=resultados" class="tab-btn {'active' if tab=='resultados' else ''}">🏆 Tabela & Resultados</a>
            </div>

            {painel_admin_html}

            {f'''
            {erro_box}
            <div style="display:grid; grid-template-columns: 2fr 1fr; gap:20px;">
                <div class="card">
                    <h3 style="margin-top:0; color:white;">Criar Nova Equipa e Preencher Participantes</h3>
                    <form action="/t/{codigo_exibicao}/adicionar-equipa" method="post" style="display:grid; grid-template-columns: 1fr 1fr; gap:15px;">
                        <div>
                            <label style="font-size:12px; color:#8b949e;">Modalidade:</label>
                            <select name="modalidade" onchange="mudarModalidadeForm(this)">{opcoes_modalidades}</select>
                            <label style="font-size:12px; color:#8b949e;">Nome da Equipa:</label><input type="text" name="nome_time" required>
                            <label style="font-size:12px; color:#8b949e;">Turma:</label><select name="serie_turma_escolhida">{opcoes_series}</select>
                            <label style="font-size:12px; color:#8b949e;">Logo URL (Opcional):</label><input type="text" name="logo_url">
                            <button type="submit" class="btn-green" style="margin-top:10px;">Criar Equipa</button>
                        </div>
                        <div>
                            <h4 style="color:#3fb950; margin-top:0; font-size:13px;">⭐ Titulares ({n_titulares})</h4>
                            {campos_titulares}
                            <h4 style="color:#58a6ff; margin-top:10px; font-size:13px;">🔄 Reservas ({n_reservas})</h4>
                            {campos_reservas}
                        </div>
                    </form>
                </div>

                <div class="card">
                    <h3 style="margin-top:0; color:white; font-size:16px;">📢 Mural de Avisos</h3>
                    {f'''
                    <form action="/t/{codigo_exibicao}/publicar-mensagem" method="post" style="margin-bottom:12px;">
                        <select name="categoria" style="padding:6px; font-size:11px;"><option value="Avisos Gerais">📢 Aviso Geral</option><option value="Regras">📜 Regras</option></select>
                        <input type="text" name="conteudo" placeholder="Escrever comunicado..." required style="padding:6px; font-size:11px;">
                        <button type="submit" style="background:#238636; color:white; border:none; padding:6px; border-radius:4px; font-weight:bold; cursor:pointer; width:100%; font-size:11px;">Publicar</button>
                    </form>
                    ''' if pode_gerir_torneio else ""}
                    <div style="max-height: 220px; overflow-y: auto;">
                        {lista_avisos_html if lista_avisos_html else "<p style='color:#8b949e; text-align:center; font-size:12px;'>Nenhum aviso publicado.</p>"}
                    </div>
                </div>
            </div>
            ''' if tab=='painel' else ""}

            {f'''
            <div class="card">
                <h3 style="margin-top:0; color:white;">Tabela de Classificação</h3>
                <table style="width:100%; border-collapse:collapse;">
                    <tr style="background:#0d1117; color:#8b949e; font-size:12px; text-align:left;">
                        <th style="padding:10px;">EQUIPA / PARTICIPANTES</th><th>MODALIDADE</th><th style="text-align:center;">PONTOS</th><th style="text-align:center;">JOGOS</th><th style="text-align:center;">AÇÃO</th>
                    </tr>
                    {linhas_tabela if linhas_tabela else "<tr><td colspan='5' style='text-align:center; padding:20px; color:#8b949e;'>Nenhuma equipa inscrita.</td></tr>"}
                </table>
            </div>
            ''' if tab=='resultados' else ""}

            {f'''
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                    <h3 style="margin:0; color:white;">Agenda de Confrontos</h3>
                    {f"<form action='/t/{codigo_exibicao}/gerar-confrontos' method='post'><button type='submit' class='btn-green' style='padding:6px 14px;'>Gerar Confrontos</button></form>" if pode_gerir_torneio else ""}
                </div>
                <div style="display:flex; flex-direction:column; gap:10px;">
                    {"".join([f'''
                    <div style="background:#0d1117; padding:12px; border-radius:8px; border:1px solid #30363d; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="background:#1f6beb; color:white; padding:2px 6px; border-radius:4px; font-size:10px;">{c[1]}</span>
                            <b style="color:white; margin-left:8px;">{c[2]} vs {c[3]}</b>
                        </div>
                        <div>
                            {f"<form action='/t/{codigo_exibicao}/atualizar-resultado' method='post' style='display:flex; gap:6px;'><input type='hidden' name='conf_id' value='{c[0]}'><input type='text' name='data_hora' value='{c[6]}' style='width:65px; padding:3px; font-size:11px;'><input type='text' name='local' value='{c[7]}' style='width:60px; padding:3px; font-size:11px;'><input type='number' name='gols1' value='{c[4]}' style='width:30px; text-align:center;'><input type='number' name='gols2' value='{c[5]}' style='width:30px; text-align:center;'><select name='status_opcao' style='width:90px; font-size:10px;'><option value='Finalizado'>Normal</option><option value='Desclassificar T1'>Punir T1</option><option value='Desclassificar T2'>Punir T2</option></select><button type='submit' style='background:#238636; color:white; border:none; padding:3px 6px; font-size:11px;'>Salvar</button></form>" if pode_gerir_torneio else f"<span style='color:#3fb950; font-weight:bold;'>{c[4]} - {c[5]}</span>"}
                        </div>
                    </div>
                    ''' for c in confrontos]) if confrontos else "<p style='color:#8b949e; text-align:center;'>Nenhum confronto gerado.</p>"}
                </div>
            </div>
            ''' if tab=='confrontos' else ""}
        </div>
    </body></html>
    """
    return resposta_html_sem_cache(html)

@app.post("/criar-torneio")
def criar_novo_torneio(request: Request, nome_novo_torneio: str = Form(...)):
    username = request.cookies.get("user") or "admin"
    ok, cod = criar_torneio_db(nome_novo_torneio.strip(), username)
    return RedirectResponse(url=f"/t/{cod}", status_code=303)

@app.post("/entrar-codigo")
def entrar_com_codigo(codigo_torneio: str = Form(...)):
    codigo_limpo = codigo_torneio.strip().upper()
    torneios = carregar_torneios_db()
    t_encontrado = next((t for t in torneios if t[2].upper() == codigo_limpo), None)
    if t_encontrado:
        return RedirectResponse(url=f"/t/{t_encontrado[2]}", status_code=303)
    return RedirectResponse(url="/?erro=Código+de+torneio+não+encontrado", status_code=303)

@app.post("/t/{codigo}/apagar-torneio")
def apagar_torneio_route(request: Request, codigo: str):
    torneios = carregar_torneios_db()
    t_atual = next((item for item in torneios if item[2].upper() == codigo.upper()), None)
    if t_atual:
        apagar_torneio_db(t_atual[0])
        restantes = carregar_torneios_db()
        if restantes:
            return RedirectResponse(url=f"/t/{restantes[0][2]}", status_code=303)
    return RedirectResponse(url="/", status_code=303)

@app.post("/t/{codigo}/adicionar-modalidade")
def ad_mod(codigo: str, nome_mod: str = Form(...), titulares: int = Form(...), reservas: int = Form(...)):
    t = next((item for item in carregar_torneios_db() if item[2].upper() == codigo.upper()), None)
    if t:
        adicionar_modalidade_db(t[0], nome_mod.strip(), titulares, reservas)
    return RedirectResponse(url=f"/t/{codigo}?tab=painel", status_code=303)

@app.post("/t/{codigo}/apagar-modalidade")
def ap_mod(codigo: str, mod_id: int = Form(...)):
    apagar_modalidade_db(mod_id)
    return RedirectResponse(url=f"/t/{codigo}?tab=painel", status_code=303)

@app.post("/t/{codigo}/adicionar-serie-turma")
def ad_st(codigo: str, nome_serie: str = Form(...), letra: str = Form(...)):
    t = next((item for item in carregar_torneios_db() if item[2].upper() == codigo.upper()), None)
    if t:
        adicionar_serie_turma_db(t[0], nome_serie.strip(), letra.upper())
    return RedirectResponse(url=f"/t/{codigo}?tab=painel", status_code=303)

@app.post("/t/{codigo}/apagar-serie-turma")
def ap_st(codigo: str, st_id: int = Form(...)):
    apagar_serie_turma_db(st_id)
    return RedirectResponse(url=f"/t/{codigo}?tab=painel", status_code=303)

@app.post("/t/{codigo}/adicionar-equipa")
async def adicionar_eq(request: Request, codigo: str):
    t = next((item for item in carregar_torneios_db() if item[2].upper() == codigo.upper()), None)
    if not t:
        return RedirectResponse(url="/", status_code=303)
        
    form_data = await request.form()
    nome_time = form_data.get("nome_time", "").strip()
    modalidade = form_data.get("modalidade", "").strip()
    serie_turma_escolhida = form_data.get("serie_turma_escolhida", "")
    logo_url = form_data.get("logo_url", "").strip()
    
    partes = serie_turma_escolhida.split(" - Turma ")
    serie = partes[0]
    turma = partes[1] if len(partes) > 1 else "A"
    
    titulares = []
    reservas = []
    for key, value in form_data.items():
        if key.startswith("titular_") and value.strip():
            titulares.append(value.strip())
        elif key.startswith("reserva_") and value.strip():
            reservas.append(value.strip())
            
    sucesso, msg = adicionar_time_db(t[0], nome_time, modalidade, serie, turma, logo_url, titulares, reservas)
    if not sucesso:
        return RedirectResponse(url=f"/t/{codigo}?tab=painel&erro_inscricao={msg}&mod_sel={modalidade}", status_code=303)
        
    return RedirectResponse(url=f"/t/{codigo}?tab=resultados", status_code=303)

@app.post("/t/{codigo}/apagar-time")
def apagar_eq(codigo: str, time_id: int = Form(...)):
    apagar_time_db(time_id)
    return RedirectResponse(url=f"/t/{codigo}?tab=resultados", status_code=303)

@app.post("/t/{codigo}/publicar-mensagem")
def pub_msg(request: Request, codigo: str, categoria: str = Form(...), conteudo: str = Form(...)):
    t = next((item for item in carregar_torneios_db() if item[2].upper() == codigo.upper()), None)
    if t:
        username = request.cookies.get("user") or "Admin"
        publicar_mensagem_db(t[0], username, categoria, conteudo)
    return RedirectResponse(url=f"/t/{codigo}?tab=painel", status_code=303)

@app.post("/t/{codigo}/apagar-mensagem")
def ap_msg(codigo: str, msg_id: int = Form(...)):
    apagar_mensagem_db(msg_id)
    return RedirectResponse(url=f"/t/{codigo}?tab=painel", status_code=303)

@app.post("/t/{codigo}/gerar-confrontos")
def gerar_conf(codigo: str):
    t = next((item for item in carregar_torneios_db() if item[2].upper() == codigo.upper()), None)
    if t:
        gerar_confrontos_automaticos(t[0])
    return RedirectResponse(url=f"/t/{codigo}?tab=confrontos", status_code=303)

@app.post("/t/{codigo}/atualizar-resultado")
def at_res(codigo: str, conf_id: int = Form(...), gols1: int = Form(...), gols2: int = Form(...), data_hora: str = Form(...), local: str = Form(...), status_opcao: str = Form(...)):
    atualizar_resultado_confronto(conf_id, gols1, gols2, data_hora, local, status_opcao)
    return RedirectResponse(url=f"/t/{codigo}?tab=confrontos", status_code=303)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="user")
    return response