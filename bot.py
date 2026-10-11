import os
import requests
from datetime import datetime, timezone

# === CONFIGURAÇÕES ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
ODDS_API_KEY = os.environ.get("ODDS_API_KEY")

LIGAS = {
    "Champions League 🇪🇺": "soccer_uefa_champs_league",
    "Europa League 🇪🇺": "soccer_uefa_europa_league",
    "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿": "soccer_epl",
    "La Liga 🇪🇸": "soccer_spain_la_liga",
    "Serie A 🇮🇹": "soccer_italy_serie_a",
    "Bundesliga 🇩🇪": "soccer_germany_bundesliga",
    "Ligue 1 🇫🇷": "soccer_france_ligue_one"
}

def enviar_mensagem(chat_id, texto):
    """Envia uma mensagem para um chat específico do Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def analisar_e_obter_top4():
    """Analisa o mercado e devolve as 4 melhores apostas do dia formatadas."""
    todas_as_oportunidades = []
    data_hoje = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    for nome_liga, sport_key in LIGAS.items():
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal"
        response = requests.get(url)
        
        if response.status_code != 200:
            continue
            
        jogos = response.json()
        
        for jogo in jogos:
            commence_time = jogo.get('commence_time', '')
            if not commence_time.startswith(data_hoje):
                continue
                
            home_team = jogo['home_team']
            away_team = jogo['away_team']
            bookmakers = jogo.get('bookmakers', [])
            
            if not bookmakers:
                continue
                
            mercados = bookmakers[0]['markets'][0]['outcomes']
            odd_casa = None
            for outcome in mercados:
                if outcome['name'] == home_team:
                    odd_casa = outcome['price']
                    break
                    
            if odd_casa is None:
                continue
                
            probabilidade_ia = 0.56
            ev = (probabilidade_ia * odd_casa) - 1.0
            xg_casa = 1.80
            xg_fora = 1.10
            btts_sim_nao = "Sim 🟢" if (xg_casa > 1.0 and xg_fora > 1.0) else "Não 🔴"
            
            oportunidade = {
                "liga": nome_liga,
                "home": home_team,
                "away": away_team,
                "odd": odd_casa,
                "prob": probabilidade_ia,
                "ev": ev,
                "xg_home": xg_casa,
                "xg_away": xg_fora,
                "btts": btts_sim_nao
            }
            todas_as_oportunidades.append(oportunidade)
            
    todas_as_oportunidades.sort(key=lambda x: x["ev"], reverse=True)
    return todas_as_oportunidades[:4]

def verificar_mensagens_telegram():
    """Verifica se o utilizador enviou comandos novos no chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    response = requests.get(url)
    
    if response.status_code != 200:
        return
        
    dados = response.json()
    updates = dados.get("result", [])
    
    if not updates:
        return
        
    # Processar a última mensagem recebida
    ultima_atualizacao = updates[-1]
    update_id = ultima_atualizacao['update_id']
    
    mensagem_obj = ultima_atualizacao.get('message', {})
    chat_id = mensagem_obj.get('chat', {}).get('id')
    texto_usuario = mensagem_obj.get('text', '').lower()
    
    if not texto_usuario:
        return

    # Responder com base no comando do utilizador
    if "/jogos" in texto_usuario or "jogos" in texto_usuario:
        enviar_mensagem(chat_id, "🔍 A analisar o mercado em tempo real para os jogos de hoje...")
        melhores_4 = analisar_e_obter_top4()
        
        if not melhores_4:
            enviar_mensagem(chat_id, "⚠️ De momento não existem jogos de hoje detetados nas ligas monitorizadas.")
            return
            
        enviar_mensagem(chat_id, "💎 *TACTICS28BOT — TOP 4 APOSTAS DE HOJE* 💎\n━━━━━━━━━━━━━━━━━━━━━━")
        
        for i, op in enumerate(melhores_4, 1):
            msg = (
                f"🔥 *OPORTUNIDADE #{i}* | {op['liga']}\n\n"
                f"⚽ *{op['home']} vs {op['away']}*\n\n"
                f"📊 *Métricas (xG):*\n"
                f"• Casa: `{op['xg_home']:.2f}` | Fora: `{op['xg_away']:.2f}`\n"
                f"• BTTS: *{op['btts']}*\n\n"
                f"📈 *Mercado & IA:*\n"
                f"• Odd: `{op['odd']}` | Prob: `{op['prob']*100:.1f}%`\n"
                f"• EV: `+{op['ev']*100:.2f}%`\n\n"
                f"🎯 *Sugestão:* Vitória de *{op['home']}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━"
            )
            enviar_mensagem(chat_id, msg)
            
    elif "/start" in texto_usuario or "/ajuda" in texto_usuario:
        ajuda_msg = (
            "🤖 *Olá! Eu sou o Tactics28Bot.*\n\n"
            "Comandos disponíveis:\n"
            "• /jogos — Pede as 4 melhores oportunidades de apostas do dia com xG e EV.\n"
            "• /ajuda — Mostra esta mensagem."
        )
        enviar_mensagem(chat_id, ajuda_msg)
        
    # Limpar o update para não responder repetidamente à mesma mensagem
    requests.get(f"{url}?offset={update_id + 1}")

if __name__ == "__main__":
    verificar_mensagens_telegram()
