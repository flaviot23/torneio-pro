from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from database import (
    init_db, obter_nome_torneio_db, atualizar_nome_torneio_db, registar_usuario, 
    verificar_login, carregar_usuarios_db, contar_usuarios_db, resetar_senha_db, alterar_papel_db, 
    apagar_usuario_db, carregar_modalidades_db, atualizar_limite_modalidade_db, 
    adicionar_modalidade_db, apagar_modalidade_db, adicionar_time_db, carregar_times_db, 
    contar_times_db, apagar_time_db, gerar_confrontos_automaticos, carregar_confrontos_db, 
    atualizar_resultado_confronto, publicar_mensagem_db, carregar_mensagens_db, apagar_mensagem_db
)

init_db()

app = FastAPI(title="Gestão de Torneios")

SESSAO_ATUAL = {"utilizador": None, "papel": None}

def resposta_html_sem_cache(html_conteudo: str):
    response = HTMLResponse(content=html_conteudo)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/", response_class=HTMLResponse)
def home(tab: str = "painel", filtro: str = "todos"):
    user = SESSAO_ATUAL["utilizador"]
    papel = SESSAO_ATUAL["papel"]
    nome_torneio = obter_nome_torneio_db()
    
    if not user:
        html_login = f"""
        <!DOCTYPE html>
        <html lang="pt">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{nome_torneio} - Acesso</title>
            <style>
                body {{ background: #0b0e14; color: #f0f6fc; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
                .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 16px; width: 380px; padding: 35px; box-shadow: 0 12px 32px rgba(0,0,0,0.5); }}
                input {{ width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #30363d; background: #0d1117; color: white; box-sizing: border-box; font-size: 14px; }}
                input:focus {{ border-color: #238636; outline: none; }}
                .btn {{ width: 100%; padding: 12px; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 15px; }}
                .btn-green {{ background: #238636; color: white; }}
                .btn-blue {{ background: #1f6beb; color: white; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2 style="color: #2ea043; text-align: center; margin: 0; font-size: 28px; font-weight: 700;">🏆 {nome_torneio}</h2>
                <p style="text-align: center; color: #8b949e; font-size: 13px; margin: 6px 0 25px 0;">Plataforma de Gestão de Campeonatos</p>
                
                <h3 style="font-size: 14px; margin-bottom: 10px; color: #c9d1d9;">Iniciar Sessão</h3>
                <form action="/login" method="post" style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 25px;">
                    <input type="text" name="username" placeholder="Nome de Utilizador" required>
                    <input type="password" name="senha" placeholder="Palavra-passe" required>
                    <button type="submit" class="btn btn-green">Entrar</button>
                </form>

                <hr style="border: 0; border-top: 1px solid #21262d; margin: 20px 0;">

                <h3 style="font-size: 14px; margin-bottom: 10px; color: #c9d1d9;">Registar Novo Utilizador</h3>
                <form action="/registar" method="post" style="display: flex; flex-direction: column; gap: 12px;">
                    <input type="text" name="username" placeholder="Escolha um Utilizador" required>
                    <input type="password" name="senha" placeholder="Palavra-passe (Mín. 6 caracteres)" required>
                    <button type="submit" class="btn btn-blue">Criar Conta</button>
                </form>
            </div>
        </body>
        </html>
        """
        return resposta_html_sem_cache(html_login)

    modalidades = carregar_modalidades_db()
    opcoes_modalidades = "".join([f"<option value='{mod[1]}'>{mod[1]} (Máx {mod[2]} atletas)</option>" for mod in modalidades])

    painel_admin_html = ""
    if papel == 'admin':
        usuarios = carregar_usuarios_db()
        lista_users_html = ""
        for u in usuarios:
            is_admin = (u[3] == 'admin')
            novo_papel_alvo = 'aluno' if is_admin else 'admin'
            texto_botao_papel = 'Tornar Aluno' if is_admin else 'Tornar Admin'
            cor_botao_papel = '#da3633' if is_admin else '#238636'
            
            botao_apagar_user = f"""
                <form action="/apagar-usuario" method="post" style="display:inline;">
                    <input type="hidden" name="user_id" value="{u[0]}">
                    <button type="submit" style="background: #da3633; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 11px;">Excluir</button>
                </form>
            """ if u[1] != 'admin' else "<span style='color: #484f58; font-size: 11px;'>Protegido</span>"

            lista_users_html += f"""
                <tr style="border-bottom: 1px solid #21262d;">
                    <td style="padding: 10px; color: #f0f6fc; font-weight: 600;">{u[1]}</td>
                    <td style="padding: 10px;"><span style="background: {'#8957e5' if is_admin else '#1f6beb'}; color: white; padding: 3px 8px; border-radius: 20px; font-size: 11px; font-weight: 700;">{u[3].upper()}</span></td>
                    <td style="padding: 10px;">
                        <form action="/alterar-papel" method="post" style="display:inline;">
                            <input type="hidden" name="user_id" value="{u[0]}">
                            <input type="hidden" name="novo_papel" value="{novo_papel_alvo}">
                            <button type="submit" style="background: {cor_botao_papel}; color: white; border: none; padding: 5px 10px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 11px;">{texto_botao_papel}</button>
                        </form>
                    </td>
                    <td style="padding: 10px;">
                        <form action="/reset-senha" method="post" style="display: flex; gap: 6px;">
                            <input type="hidden" name="user_id" value="{u[0]}">
                            <input type="text" name="nova_senha" placeholder="Nova senha" required style="padding: 4px 6px; background: #0d1117; color: white; border: 1px solid #30363d; border-radius: 6px; width: 90px; font-size: 11px;">
                            <button type="submit" style="background: #d29922; color: white; border: none; padding: 4px 6px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 11px;">Redefinir</button>
                        </form>
                    </td>
                    <td style="padding: 10px; text-align: center;">{botao_apagar_user}</td>
                </tr>
            """

        lista_mods_html = ""
        for mod in modalidades:
            lista_mods_html += f"""
                <tr style="border-bottom: 1px solid #21262d;">
                    <td style="padding: 10px; color: #f0f6fc; font-weight: 600;">{mod[1]}</td>
                    <td style="padding: 10px;">
                        <form action="/atualizar-limite" method="post" style="display: flex; gap: 8px; align-items: center;">
                            <input type="hidden" name="mod_id" value="{mod[0]}">
                            <input type="number" name="novo_limite" value="{mod[2]}" min="1" max="50" style="padding: 5px; width: 70px; background: #0d1117; color: white; border: 1px solid #30363d; border-radius: 6px; text-align: center; font-size: 13px;">
                            <button type="submit" style="background: #238636; color: white; border: none; padding: 5px 10px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 11px;">Salvar</button>
                        </form>
                    </td>
                    <td style="padding: 10px; text-align: center;">
                        <form action="/apagar-modalidade" method="post" style="display:inline;">
                            <input type="hidden" name="mod_id" value="{mod[0]}">
                            <button type="submit" style="background: #da3633; color: white; border: none; padding: 5px 10px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 11px;">Remover</button>
                        </form>
                    </td>
                </tr>
            """
        
        painel_admin_html = f"""
        <div style="background: #161b22; padding: 25px; border-radius: 12px; margin-top: 25px; border: 1px solid #d29922; box-shadow: 0 8px 24px rgba(0,0,0,0.4);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 12px; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 22px;">🛡️</span>
                    <h2 style="color: #d29922; margin: 0; font-size: 20px; font-weight: 700;">Painel de Administração Avançado</h2>
                </div>
                <form action="/atualizar-nome-torneio" method="post" style="display: flex; gap: 8px; align-items: center;">
                    <input type="text" name="novo_nome" value="{nome_torneio}" required placeholder="Nome do Torneio" style="padding: 6px 10px; font-size: 12px; width: 180px;">
                    <button type="submit" style="background: #1f6beb; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 12px;">Alterar Nome</button>
                </form>
            </div>

            <div style="display: flex; gap: 25px; flex-wrap: wrap; margin-top: 20px;">
                <div style="flex: 1.5; min-width: 380px;">
                    <h3 style="color: #c9d1d9; font-size: 15px; margin-bottom: 10px;">Gestão de Utilizadores, Permissões e Exclusão</h3>
                    <div style="overflow-x: auto; max-height: 250px; overflow-y: auto;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background: #0d1117; text-align: left; color: #8b949e; font-size: 11px; text-transform: uppercase;">
                                    <th style="padding: 8px;">Utilizador</th>
                                    <th style="padding: 8px;">Cargo</th>
                                    <th style="padding: 8px;">Permissão</th>
                                    <th style="padding: 8px;">Senha</th>
                                    <th style="padding: 8px; text-align: center;">Excluir</th>
                                </tr>
                            </thead>
                            <tbody>{lista_users_html}</tbody>
                        </table>
                    </div>
                </div>
                <div style="flex: 1; min-width: 300px;">
                    <h3 style="color: #c9d1d9; font-size: 15px; margin-bottom: 10px;">Gerir Limites por Modalidade</h3>
                    <form action="/adicionar-modalidade" method="post" style="display: flex; gap: 8px; margin-bottom: 12px;">
                        <input type="text" name="nome_mod" placeholder="Nova modalidade..." required style="flex: 2; padding: 6px 10px; font-size: 12px;">
                        <input type="number" name="limite_mod" placeholder="Máx" value="10" min="1" required style="flex: 1; padding: 6px 10px; font-size: 12px; text-align: center;">
                        <button type="submit" style="background: #1f6beb; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 12px;">Adicionar</button>
                    </form>
                    <div style="overflow-x: auto; max-height: 200px; overflow-y: auto;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background: #0d1117; text-align: left; color: #8b949e; font-size: 11px; text-transform: uppercase;">
                                    <th style="padding: 8px;">Modalidade</th>
                                    <th style="padding: 8px;">Limite</th>
                                    <th style="padding: 8px; text-align: center;">Ação</th>
                                </tr>
                            </thead>
                            <tbody>{lista_mods_html}</tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        """

    total_equipas = contar_times_db()
    total_usuarios = contar_usuarios_db()
    times = carregar_times_db()

    linhas_tabela = ""
    for t in times:
        botao_apagar = f"""<form action="/apagar-time" method="post" style="display:inline;"><input type="hidden" name="nome_time" value="{t[0]}"><button type="submit" style="background: #da3633; color:white; border:none; padding:6px 12px; border-radius:6px; cursor:pointer; font-weight:600; font-size:12px;">Apagar</button></form>""" if papel == 'admin' else "<span style='color: #484f58; font-size: 12px;'>Protegido</span>"
        linhas_tabela += f"""
            <tr style="border-bottom: 1px solid #21262d;">
                <td style="padding: 14px; color: #f0f6fc; font-weight: 600;">{t[0]}</td>
                <td style="padding: 14px;"><span style="background: #1f6beb; color: white; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600;">{t[1]}</span></td>
                <td style="padding: 14px; text-align: center; color: #3fb950; font-weight: 700; font-size: 16px;">{t[2]}</td>
                <td style="padding: 14px; text-align: center; color: #c9d1d9;">{t[3]}</td>
                <td style="padding: 14px; text-align: center;">{botao_apagar}</td>
            </tr>
        """
    if not linhas_tabela:
        linhas_tabela = "<tr><td colspan='5' style='text-align: center; padding: 30px; color: #8b949e;'>Nenhuma equipa registada no torneio até ao momento.</td></tr>"

    confrontos = carregar_confrontos_db()
    
    confrontos_por_mod = {}
    for c in confrontos:
        mod = c[1]
        if mod not in confrontos_por_mod:
            confrontos_por_mod[mod] = []
        confrontos_por_mod[mod].append(c)

    confrontos_html_por_parte = ""
    if not confrontos:
        confrontos_html_por_parte = "<p style='color: #8b949e; text-align: center; padding: 40px;'>Ainda não foram gerados confrontos. Clique no botão acima para gerar automaticamente.</p>"
    else:
        for mod, confs in confrontos_por_mod.items():
            linhas_mod = ""
            for c in confs:
                status_cor = '#3fb950' if 'Finalizado' in c[6] else '#d29922'
                
                opcoes_vencedor = f"""
                    <option value="">-- Vencedor Automático (Placar) --</option>
                    <option value="{c[2]}" {'selected' if c[7]==c[2] else ''}>{c[2]}</option>
                    <option value="{c[3]}" {'selected' if c[7]==c[3] else ''}>{c[3]}</option>
                """
                
                gabarito_edicao = f"""
                    <form action="/atualizar-resultado" method="post" style="display: flex; flex-direction: column; gap: 6px; align-items: center; background: #161b22; padding: 8px; border-radius: 6px; border: 1px solid #30363d;">
                        <input type="hidden" name="conf_id" value="{c[0]}">
                        <div style="display: flex; gap: 4px; align-items: center;">
                            <input type="number" name="gols1" value="{c[4]}" min="0" style="width: 40px; text-align: center; background: #0d1117; color: white; border: 1px solid #30363d; border-radius: 4px; padding: 3px;">
                            <span>x</span>
                            <input type="number" name="gols2" value="{c[5]}" min="0" style="width: 40px; text-align: center; background: #0d1117; color: white; border: 1px solid #30363d; border-radius: 4px; padding: 3px;">
                        </div>
                        <div style="display: flex; gap: 4px; width: 100%; align-items: center;">
                            <select name="vencedor_manual" style="font-size: 11px; padding: 3px; background: #0d1117; color: white; border: 1px solid #30363d; border-radius: 4px; flex: 1;">
                                {opcoes_vencedor}
                            </select>
                            <button type="submit" style="background: #1f6beb; color: white; border: none; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: bold;">Salvar</button>
                        </div>
                    </form>
                """ if papel == 'admin' else f"<b style='color: #fff;'>{c[4]} x {c[5]}</b><br><span style='font-size:11px; color:#8b949e;'>Vencedor: {c[7] or 'A definir'}</span>"

                linhas_mod += f"""
                    <tr style="border-bottom: 1px solid #21262d;">
                        <td style="padding: 12px; text-align: right; color: #f0f6fc; font-weight: bold;">{c[2]}</td>
                        <td style="padding: 12px; text-align: center; min-width: 200px;">{gabarito_edicao}</td>
                        <td style="padding: 12px; text-align: left; color: #f0f6fc; font-weight: bold;">{c[3]}</td>
                        <td style="padding: 12px; text-align: center;"><span style="background: {status_cor}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{c[6]}</span></td>
                    </tr>
                """

            confrontos_html_por_parte += f"""
                <div style="background: #0d1117; border: 1px solid #30363d; border-radius: 10px; padding: 20px; margin-bottom: 25px;">
                    <h4 style="color: #58a6ff; margin-top: 0; font-size: 16px; border-bottom: 1px solid #30363d; padding-bottom: 8px;">⚽ Modalidade: {mod}</h4>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="text-align: left; color: #8b949e; font-size: 11px; text-transform: uppercase;">
                                <th style="padding: 8px; text-align: right;">Equipa A</th>
                                <th style="padding: 8px; text-align: center;">Placar & Vencedor Manual</th>
                                <th style="padding: 8px; text-align: left;">Equipa B</th>
                                <th style="padding: 8px; text-align: center;">Estado</th>
                            </tr>
                        </thead>
                        <tbody>{linhas_mod}</tbody>
                    </table>
                </div>
            """

    btn_gerar_confrontos = f"""
        <form action="/gerar-confrontos" method="post" style="margin-bottom: 20px;">
            <button type="submit" style="background: #238636; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 14px;">⚡ Gerar Confrontos & W.O. Automático</button>
        </form>
    """ if papel == 'admin' else ""

    chaveamento_por_parte = ""
    if not confrontos:
        chaveamento_por_parte = "<p style='color: #8b949e; text-align: center; padding: 40px;'>Nenhum chaveamento gerado ainda.</p>"
    else:
        for mod, confs in confrontos_por_mod.items():
            cards_mod = ""
            for c in confs:
                vencedor = "A definir"
                if c[7]:
                    vencedor = f"🏆 {c[7]}"
                elif 'Finalizado' in c[6]:
                    if c[4] > c[5]: vencedor = f"🏆 {c[2]}"
                    elif c[5] > c[4]: vencedor = f"🏆 {c[3]}"
                    else: vencedor = "Empate / Penáltis"

                cards_mod += f"""
                    <div style="background: #0d1117; border: 1px solid #30363d; border-radius: 10px; padding: 15px; width: 260px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                        <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #21262d; font-size: 14px;">
                            <span>{c[2]}</span> <b>{c[4]}</b>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 6px 0; font-size: 14px;">
                            <span>{c[3]}</span> <b>{c[5]}</b>
                        </div>
                        <div style="margin-top: 10px; font-size: 12px; color: #3fb950; text-align: center; background: #161b22; padding: 5px; border-radius: 6px;">
                            Vencedor: <b>{vencedor}</b>
                        </div>
                    </div>
                """

            chaveamento_por_parte += f"""
                <div style="background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; margin-bottom: 25px;">
                    <h4 style="color: #3fb950; margin-top: 0; font-size: 18px; border-bottom: 1px solid #30363d; padding-bottom: 8px;">🌳 Chaveamento: {mod}</h4>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-top: 15px;">{cards_mod}</div>
                </div>
            """

    conteudo_aba = ""
    if tab == "confrontos":
        conteudo_aba = f"""
            <div class="card">
                <h3 style="margin-top: 0; color: #f0f6fc; font-size: 18px; font-weight: 700; margin-bottom: 15px;">⚔️ Gestão de Confrontos e W.O. por Modalidade</h3>
                {btn_gerar_confrontos}
                <div>{confrontos_html_por_parte}</div>
            </div>
        """
    elif tab == "chaveamento":
        conteudo_aba = f"""
            <div class="card">
                <h3 style="margin-top: 0; color: #f0f6fc; font-size: 18px; font-weight: 700; margin-bottom: 15px;">🌳 Chaveamento Oficial (Mata-Mata) por Modalidade</h3>
                <p style="color: #8b949e; font-size: 13px; margin-bottom: 20px;">Visualização dividida por cada modalidade desportiva.</p>
                <div>{chaveamento_por_parte}</div>
            </div>
        """
    else:
        mensagens = carregar_mensagens_db()
        mensagens_filtradas = []
        for m in mensagens:
            if filtro == "todos": mensagens_filtradas.append(m)
            elif filtro == "jogos" and m[2] == "Resultados & Jogos": mensagens_filtradas.append(m)
            elif filtro == "datas" and m[2] == "Datas & Prazos": mensagens_filtradas.append(m)
            elif filtro == "avisos" and m[2] == "Avisos Gerais": mensagens_filtradas.append(m)

        lista_mural_html = ""
        for m in mensagens_filtradas:
            btn_del_msg = f"""<form action="/apagar-msg" method="post" style="display:inline;"><input type="hidden" name="msg_id" value="{m[0]}"><button type="submit" style="background: #da3633; color:white; border:none; padding:2px 6px; border-radius:4px; font-size:10px; cursor:pointer; font-weight:bold;">X</button></form>""" if papel == 'admin' else ""
            conteudo_seguro = m[3].replace('"', '&quot;').replace("'", "&#39;")
            badge_cor = "#58a6ff" if m[2] == "Avisos Gerais" else ("#3fb950" if m[2] == "Resultados & Jogos" else "#d29922")
            
            lista_mural_html += f"""
                <div style="background: #0d1117; padding: 12px; border-radius: 8px; margin-bottom: 10px; border: 1px solid #30363d; border-left: 4px solid {badge_cor};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <div>
                            <span style="background: {badge_cor}; color: #000; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; margin-right: 6px;">{m[2]}</span>
                            <strong style="color: #c9d1d9; font-size: 12px;">{m[1]}</strong>
                        </div>
                        <div style="display: flex; gap: 6px; align-items: center;">
                            <button onclick="abrirModal('{m[1]}', '{m[2]}', '{conteudo_seguro}')" style="background: #21262d; color: #58a6ff; border: 1px solid #30363d; border-radius: 4px; padding: 2px 6px; font-size: 11px; cursor: pointer;">🔍 Lupa</button>
                            {btn_del_msg}
                        </div>
                    </div>
                    <p style="margin: 0; color: #f0f6fc; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 400px;">{m[3]}</p>
                </div>
            """

        if not lista_mural_html:
            lista_mural_html = "<p style='color: #8b949e; text-align: center; margin-top: 40px; font-size: 13px;'>Nenhuma publicação encontrada nesta categoria.</p>"

        form_publicacao_html = ""
        if papel == 'admin':
            form_publicacao_html = f"""
                <form action="/enviar-msg" method="post" style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 15px; background: #0d1117; padding: 12px; border-radius: 8px; border: 1px solid #30363d;">
                    <select name="categoria" style="padding: 6px; font-size: 12px;">
                        <option value="Avisos Gerais">📢 Avisos Gerais</option>
                        <option value="Resultados & Jogos">⚽ Resultados & Jogos</option>
                        <option value="Datas & Prazos">📅 Datas & Prazos</option>
                    </select>
                    <div style="display: flex; gap: 8px;">
                        <input type="text" name="conteudo" placeholder="Escreva o comunicado oficial..." required style="flex: 1; padding: 8px; font-size: 13px;">
                        <button type="submit" class="btn-action btn-blue" style="padding: 8px 14px; font-size: 13px;">Publicar</button>
                    </div>
                </form>
            """

        btn_todos = "background: #1f6beb; color: white;" if filtro == "todos" else "background: #21262d; color: #c9d1d9;"
        btn_jogos = "background: #3fb950; color: white;" if filtro == "jogos" else "background: #21262d; color: #c9d1d9;"
        btn_datas = "background: #d29922; color: white;" if filtro == "datas" else "background: #21262d; color: #c9d1d9;"
        btn_avisos = "background: #58a6ff; color: white;" if filtro == "avisos" else "background: #21262d; color: #c9d1d9;"

        conteudo_aba = f"""
            <div style="display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap;">
                <div style="flex: 1; background: #161b22; padding: 18px 22px; border-radius: 10px; border: 1px solid #30363d; border-left: 4px solid #3fb950;">
                    <span style="color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase;">Equipas Inscritas</span>
                    <h3 style="margin: 6px 0 0 0; color: #3fb950; font-size: 24px; font-weight: 800;">{total_equipas}</h3>
                </div>
                <div style="flex: 1; background: #161b22; padding: 18px 22px; border-radius: 10px; border: 1px solid #30363d; border-left: 4px solid #58a6ff;">
                    <span style="color: #8b949e; font-size: 11px; font-weight: 700; text-transform: uppercase;">Utilizadores Registados</span>
                    <h3 style="margin: 6px 0 0 0; color: #58a6ff; font-size: 24px; font-weight: 800;">{total_usuarios}</h3>
                </div>
            </div>

            {painel_admin_html}

            <div style="display: flex; gap: 20px; margin-top: 25px; flex-wrap: wrap;">
                <div class="card" style="flex: 1; min-width: 320px;">
                    <h3 style="margin-top: 0; color: #f0f6fc; border-bottom: 2px solid #238636; padding-bottom: 10px; font-size: 17px; font-weight: 700;">Registar Equipa</h3>
                    <form action="/adicionar-equipa" method="post" style="display: flex; flex-direction: column; gap: 14px; margin-top: 15px;">
                        <div>
                            <label style="font-size: 13px; color: #8b949e; display: block; margin-bottom: 6px;">Nome da Equipa:</label>
                            <input type="text" name="nome_time" placeholder="ex: Leões FC" required>
                        </div>
                        <div>
                            <label style="font-size: 13px; color: #8b949e; display: block; margin-bottom: 6px;">Selecione a Modalidade:</label>
                            <select name="modalidade">{opcoes_modalidades}</select>
                        </div>
                        <button type="submit" class="btn-action btn-green" style="margin-top: 5px;">Inscrever Equipa no Torneio</button>
                    </form>
                </div>

                <div class="card" style="flex: 1.3; min-width: 350px;">
                    <h3 style="margin-top: 0; color: #f0f6fc; border-bottom: 2px solid #1f6beb; padding-bottom: 10px; font-size: 17px; font-weight: 700;">Mural Oficial de Avisos e Jogos</h3>
                    
                    <div style="display: flex; gap: 6px; margin-bottom: 15px; flex-wrap: wrap;">
                        <a href="/?tab=painel&filtro=todos" style="padding: 5px 10px; border-radius: 6px; text-decoration: none; font-size: 11px; font-weight: bold; {btn_todos}">🌐 Todos</a>
                        <a href="/?tab=painel&filtro=jogos" style="padding: 5px 10px; border-radius: 6px; text-decoration: none; font-size: 11px; font-weight: bold; {btn_jogos}">⚽ Jogos</a>
                        <a href="/?tab=painel&filtro=datas" style="padding: 5px 10px; border-radius: 6px; text-decoration: none; font-size: 11px; font-weight: bold; {btn_datas}">📅 Datas</a>
                        <a href="/?tab=painel&filtro=avisos" style="padding: 5px 10px; border-radius: 6px; text-decoration: none; font-size: 11px; font-weight: bold; {btn_avisos}">📢 Avisos</a>
                    </div>

                    {form_publicacao_html}

                    <div style="max-height: 250px; overflow-y: auto; padding-right: 5px;">
                        {lista_mural_html}
                    </div>
                </div>
            </div>

            <div class="card" style="margin-top: 25px;">
                <h3 style="margin-top: 0; color: #f0f6fc; font-size: 18px; font-weight: 700; margin-bottom: 15px;">Equipas Inscritas</h3>
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #0d1117; text-align: left; color: #8b949e; font-size: 12px; text-transform: uppercase;">
                                <th style="padding: 12px;">Equipa</th>
                                <th style="padding: 12px;">Modalidade</th>
                                <th style="padding: 12px; text-align: center;">Pontos</th>
                                <th style="padding: 12px; text-align: center;">Jogos</th>
                                <th style="padding: 12px; text-align: center;">Ações</th>
                            </tr>
                        </thead>
                        <tbody>{linhas_tabela}</tbody>
                    </table>
                </div>
            </div>
        """

    active_painel = "background: #238636; color: white;" if tab == "painel" else "background: #21262d; color: #c9d1d9;"
    active_conf = "background: #238636; color: white;" if tab == "confrontos" else "background: #21262d; color: #c9d1d9;"
    active_chave = "background: #238636; color: white;" if tab == "chaveamento" else "background: #21262d; color: #c9d1d9;"

    html_final = f"""
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{nome_torneio} - Painel Geral</title>
        <style>
            body {{ background-color: #0b0e14; color: #f0f6fc; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; margin: 0; padding: 30px 15px; }}
            .container {{ max-width: 1050px; margin: auto; }}
            .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 25px; box-shadow: 0 4px 16px rgba(0,0,0,0.3); }}
            input, select, textarea {{ width: 100%; padding: 10px 12px; border-radius: 6px; border: 1px solid #30363d; background: #0d1117; color: white; box-sizing: border-box; font-size: 14px; }}
            input:focus, select:focus, textarea:focus {{ border-color: #3fb950; outline: none; }}
            .btn-action {{ padding: 10px 18px; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px; transition: 0.2s; }}
            .btn-green {{ background: #238636; color: white; }}
            .btn-blue {{ background: #1f6beb; color: white; }}
            .nav-tab {{ padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 13px; }}
            
            .modal-overlay {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); justify-content: center; align-items: center; z-index: 1000; }}
            .modal-content {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; width: 90%; max-width: 500px; padding: 25px; box-shadow: 0 12px 32px rgba(0,0,0,0.6); }}
        </style>
        <script>
            function abrirModal(autor, categoria, texto) {{
                document.getElementById('modalAutor').innerText = "Autor: " + autor;
                document.getElementById('modalCategoria').innerText = "Categoria: " + categoria;
                document.getElementById('modalTexto').innerText = texto;
                document.getElementById('modalAviso').style.display = 'flex';
            }}
            function fecharModal() {{
                document.getElementById('modalAviso').style.display = 'none';
            }}
        </script>
    </head>
    <body>
        <div class="container">
            
            <div style="display: flex; justify-content: space-between; align-items: center; background: #161b22; padding: 20px 25px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 20px; flex-wrap: wrap; gap: 15px;">
                <div>
                    <h1 style="color: #3fb950; margin: 0; font-size: 26px; font-weight: 800;">🏆 {nome_torneio}</h1>
                    <p style="margin: 4px 0 0 0; color: #8b949e; font-size: 13px;">Sistema Automatizado de Gestão de Torneios</p>
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <div style="text-align: right;">
                        <span style="display: block; font-size: 14px; color: #f0f6fc; font-weight: 600;">{user}</span>
                        <span style="font-size: 10px; background: {'#8957e5' if papel=='admin' else '#1f6beb'}; padding: 2px 8px; border-radius: 12px; font-weight: 800;">{papel.upper()}</span>
                    </div>
                    <a href="/logout" style="background: #da3633; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: 600;">Sair</a>
                </div>
            </div>

            <div style="display: flex; gap: 10px; margin-bottom: 25px; flex-wrap: wrap;">
                <a href="/?tab=painel" class="nav-tab" style="{active_painel}">🏠 Painel & Inscrições</a>
                <a href="/?tab=confrontos" class="nav-tab" style="{active_conf}">⚔️ Confrontos & Jogos</a>
                <a href="/?tab=chaveamento" class="nav-tab" style="{active_chave}">🌳 Chaveamento / Mata-Mata</a>
            </div>

            {conteudo_aba}

        </div>

        <div id="modalAviso" class="modal-overlay">
            <div class="modal-content">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-bottom: 15px;">
                    <h3 style="margin: 0; color: #3fb950; font-size: 18px;">🔍 Detalhe do Comunicado</h3>
                    <button onclick="fecharModal()" style="background: #da3633; color: white; border: none; border-radius: 6px; padding: 4px 10px; cursor: pointer; font-weight: bold;">X</button>
                </div>
                <div style="margin-bottom: 15px;">
                    <span id="modalCategoria" style="background: #1f6beb; color: white; font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: bold;"></span>
                    <span id="modalAutor" style="color: #8b949e; font-size: 12px; margin-left: 10px;"></span>
                </div>
                <p id="modalTexto" style="color: #f0f6fc; font-size: 15px; line-height: 1.5; background: #0d1117; padding: 15px; border-radius: 8px; border: 1px solid #30363d; word-break: break-word;"></p>
                <div style="text-align: right; margin-top: 20px;">
                    <button onclick="fecharModal()" class="btn-action btn-blue" style="padding: 6px 16px; font-size: 13px;">Fechar</button>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return resposta_html_sem_cache(html_final)

@app.post("/atualizar-nome-torneio")
def atualizar_nome_torneio(novo_nome: str = Form(...)):
    if SESSAO_ATUAL["papel"] == 'admin':
        atualizar_nome_torneio_db(novo_nome.strip())
    return RedirectResponse(url="/", status_code=303)

@app.post("/registar")
def registar(username: str = Form(...), senha: str = Form(...)):
    senhas_fracas = ["123456", "senha123", "admin", "abc12345", "12345678"]
    if len(senha) < 6 or senha in senhas_fracas:
        return resposta_html_sem_cache("<script>alert('Aviso: Esta palavra-passe é fraca ou curta!'); window.location.href='/';</script>")
    sucesso, mensagem = registar_usuario(username, senha)
    if not sucesso: return resposta_html_sem_cache(f"<script>alert('{mensagem}'); window.location.href='/';</script>")
    SESSAO_ATUAL["utilizador"] = username
    SESSAO_ATUAL["papel"] = "aluno"
    return RedirectResponse(url="/", status_code=303)

@app.post("/login")
def login(username: str = Form(...), senha: str = Form(...)):
    papel = verificar_login(username, senha)
    if papel:
        SESSAO_ATUAL["utilizador"] = username
        SESSAO_ATUAL["papel"] = papel
        return RedirectResponse(url="/", status_code=303)
    return resposta_html_sem_cache("<script>alert('Utilizador ou palavra-passe incorretos!'); window.location.href='/';</script>")

@app.get("/logout")
def logout():
    SESSAO_ATUAL["utilizador"] = None
    SESSAO_ATUAL["papel"] = None
    return RedirectResponse(url="/", status_code=303)

@app.post("/alterar-papel")
def alterar_papel(user_id: int = Form(...), novo_papel: str = Form(...)):
    if SESSAO_ATUAL["papel"] == 'admin': alterar_papel_db(user_id, novo_papel)
    return RedirectResponse(url="/", status_code=303)

@app.post("/apagar-usuario")
def apagar_usuario(user_id: int = Form(...)):
    if SESSAO_ATUAL["papel"] == 'admin':
        apagar_usuario_db(user_id)
    return RedirectResponse(url="/", status_code=303)

@app.post("/atualizar-limite")
def atualizar_limite(mod_id: int = Form(...), novo_limite: int = Form(...)):
    if SESSAO_ATUAL["papel"] == 'admin': atualizar_limite_modalidade_db(mod_id, novo_limite)
    return RedirectResponse(url="/", status_code=303)

@app.post("/adicionar-modalidade")
def adicionar_modalidade(nome_mod: str = Form(...), limite_mod: int = Form(...)):
    if SESSAO_ATUAL["papel"] == 'admin': adicionar_modalidade_db(nome_mod.strip(), limite_mod)
    return RedirectResponse(url="/", status_code=303)

@app.post("/apagar-modalidade")
def apagar_modalidade(mod_id: int = Form(...)):
    if SESSAO_ATUAL["papel"] == 'admin': apagar_modalidade_db(mod_id)
    return RedirectResponse(url="/", status_code=303)

@app.post("/adicionar-equipa")
def adicionar_equipa(nome_time: str = Form(...), modalidade: str = Form(...)):
    sucesso, mensagem = adicionar_time_db(nome_time.strip(), modalidade)
    if not sucesso: return resposta_html_sem_cache(f"<script>alert('{mensagem}'); window.location.href='/';</script>")
    return RedirectResponse(url="/", status_code=303)

@app.post("/apagar-time")
def apagar_time(nome_time: str = Form(...)):
    if SESSAO_ATUAL["papel"] == 'admin': apagar_time_db(nome_time)
    return RedirectResponse(url="/", status_code=303)

@app.post("/gerar-confrontos")
def gerar_confrontos():
    if SESSAO_ATUAL["papel"] == 'admin':
        sucesso, msg = gerar_confrontos_automaticos()
        return resposta_html_sem_cache(f"<script>alert('{msg}'); window.location.href='/?tab=confrontos';</script>")
    return RedirectResponse(url="/?tab=confrontos", status_code=303)

@app.post("/atualizar-resultado")
def atualizar_resultado(conf_id: int = Form(...), gols1: int = Form(...), gols2: int = Form(...), vencedor_manual: str = Form(None)):
    if SESSAO_ATUAL["papel"] == 'admin':
        atualizar_resultado_confronto(conf_id, gols1, gols2, vencedor_manual)
    return RedirectResponse(url="/?tab=confrontos", status_code=303)

@app.post("/enviar-msg")
def enviar_msg(categoria: str = Form(...), conteudo: str = Form(...)):
    if SESSAO_ATUAL["papel"] == 'admin':
        autor = SESSAO_ATUAL["utilizador"] or "Admin"
        publicar_mensagem_db(autor, categoria, conteudo)
    return RedirectResponse(url="/", status_code=303)

@app.post("/apagar-msg")
def apagar_msg(msg_id: int = Form(...)):
    if SESSAO_ATUAL["papel"] == 'admin': apagar_mensagem_db(msg_id)
    return RedirectResponse(url="/", status_code=303)

@app.post("/reset-senha")
def reset_senha(user_id: int = Form(...), nova_senha: str = Form(...)):
    if SESSAO_ATUAL["papel"] == 'admin': resetar_senha_db(user_id, nova_senha)
    return RedirectResponse(url="/", status_code=303)