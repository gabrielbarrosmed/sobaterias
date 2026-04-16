"""
Painel diário de eventos - Só Baterias
Gera um relatório HTML com os eventos dos últimos 30 dias.
Execute: python painel-ga4.py
"""
import json, os, webbrowser
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, Dimension, Metric, DateRange, FilterExpression,
    Filter, FilterExpressionList
)

TOKEN_FILE = "C:/Projetos Claude/mcp-for-gtm/token.json"
PROPERTY_ID = "390883874"
EVENTOS = ["whatsapp_click", "click_ligar", "scroll_depth", "tempo_30s_pagina", "page_view"]

# Autenticação
creds = Credentials.from_authorized_user_file(TOKEN_FILE)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())

client = BetaAnalyticsDataClient(credentials=creds)

# Buscar dados dos últimos 30 dias por evento e data
request = RunReportRequest(
    property=f"properties/{PROPERTY_ID}",
    dimensions=[Dimension(name="eventName"), Dimension(name="date")],
    metrics=[Metric(name="eventCount")],
    date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
    dimension_filter=FilterExpression(
        or_group=FilterExpressionList(
            expressions=[
                FilterExpression(filter=Filter(
                    field_name="eventName",
                    string_filter=Filter.StringFilter(value=e, match_type="EXACT")
                )) for e in EVENTOS
            ]
        )
    )
)

response = client.run_report(request)

# Organizar dados
dados = {}
for row in response.rows:
    evento = row.dimension_values[0].value
    data = row.dimension_values[1].value
    contagem = int(row.metric_values[0].value)
    data_fmt = f"{data[6:8]}/{data[4:6]}/{data[0:4]}"
    if evento not in dados:
        dados[evento] = {}
    dados[evento][data_fmt] = contagem

# Totais
totais = {e: sum(dados.get(e, {}).values()) for e in EVENTOS}

# Gerar HTML
hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Painel Só Baterias — GA4</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #f0f2f5; color: #333; }}
  header {{ background: #1a1a2e; color: white; padding: 24px 32px; }}
  header h1 {{ font-size: 22px; font-weight: 700; }}
  header p {{ font-size: 13px; opacity: 0.6; margin-top: 4px; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; padding: 32px; }}
  .card {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
  .card .label {{ font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
  .card .value {{ font-size: 36px; font-weight: 700; color: #1a1a2e; }}
  .card .icon {{ font-size: 28px; margin-bottom: 8px; }}
  .card.green .value {{ color: #22c55e; }}
  .card.blue .value {{ color: #3b82f6; }}
  .card.orange .value {{ color: #f97316; }}
  .card.purple .value {{ color: #a855f7; }}
  .card.gray .value {{ color: #64748b; }}
  table {{ width: calc(100% - 64px); margin: 0 32px 32px; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-collapse: collapse; overflow: hidden; }}
  th {{ background: #1a1a2e; color: white; padding: 12px 16px; text-align: left; font-size: 13px; }}
  td {{ padding: 10px 16px; font-size: 14px; border-bottom: 1px solid #f0f0f0; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #f8faff; }}
  .tag {{ display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: 11px; font-weight: 600; }}
  .tag.green {{ background: #dcfce7; color: #166534; }}
  .tag.blue {{ background: #dbeafe; color: #1e40af; }}
  .tag.orange {{ background: #ffedd5; color: #9a3412; }}
  .tag.purple {{ background: #f3e8ff; color: #6b21a8; }}
  .tag.gray {{ background: #f1f5f9; color: #475569; }}
</style>
</head>
<body>
<header>
  <h1>Só Baterias — Painel de Eventos</h1>
  <p>Últimos 30 dias · Atualizado em {hoje}</p>
</header>

<div class="cards">
  <div class="card green">
    <div class="icon">💬</div>
    <div class="label">WhatsApp Click</div>
    <div class="value">{totais.get('whatsapp_click', 0)}</div>
  </div>
  <div class="card blue">
    <div class="icon">📞</div>
    <div class="label">Cliques em Ligar</div>
    <div class="value">{totais.get('click_ligar', 0)}</div>
  </div>
  <div class="card orange">
    <div class="icon">📜</div>
    <div class="label">Scroll Depth</div>
    <div class="value">{totais.get('scroll_depth', 0)}</div>
  </div>
  <div class="card purple">
    <div class="icon">⏱️</div>
    <div class="label">30s na Página</div>
    <div class="value">{totais.get('tempo_30s_pagina', 0)}</div>
  </div>
  <div class="card gray">
    <div class="icon">👁️</div>
    <div class="label">Pageviews</div>
    <div class="value">{totais.get('page_view', 0)}</div>
  </div>
</div>

<table>
  <tr>
    <th>Data</th>
    <th>WhatsApp</th>
    <th>Ligar</th>
    <th>Scroll</th>
    <th>30s Página</th>
    <th>Pageviews</th>
  </tr>
"""

# Coletar todas as datas únicas ordenadas
todas_datas = sorted(set(
    d for e in dados.values() for d in e.keys()
), key=lambda x: x[6:]+x[3:5]+x[:2], reverse=True)

for data in todas_datas:
    html += f"""  <tr>
    <td><strong>{data}</strong></td>
    <td><span class="tag green">{dados.get('whatsapp_click', {}).get(data, 0)}</span></td>
    <td><span class="tag blue">{dados.get('click_ligar', {}).get(data, 0)}</span></td>
    <td><span class="tag orange">{dados.get('scroll_depth', {}).get(data, 0)}</span></td>
    <td><span class="tag purple">{dados.get('tempo_30s_pagina', {}).get(data, 0)}</span></td>
    <td><span class="tag gray">{dados.get('page_view', {}).get(data, 0)}</span></td>
  </tr>
"""

html += """</table>
</body>
</html>"""

# Salvar e abrir
output = "C:/Projetos Claude/SITES/painel-ga4.html"
with open(output, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Painel gerado: {output}")
webbrowser.open(f"file:///{output}")
