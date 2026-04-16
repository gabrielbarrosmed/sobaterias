"""
Painel GA4 — Só Baterias
Dashboard web com filtro de datas.
Execute: python painel-server.py
Acesse: http://localhost:5000
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, Dimension, Metric, DateRange,
    FilterExpression, Filter, FilterExpressionList
)

TOKEN_FILE = "C:/Projetos Claude/mcp-for-gtm/token.json"
PROPERTY_ID = "390883874"
EVENTOS = ["whatsapp_click", "click_ligar", "scroll_depth", "tempo_30s_pagina", "page_view"]

app = Flask(__name__)
CORS(app)


def get_client():
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return BetaAnalyticsDataClient(credentials=creds)


HTML = open("painel-dashboard.html", encoding="utf-8").read()


@app.route("/")
def index():
    return HTML


@app.route("/api/dados")
def dados():
    start = request.args.get("start", "30daysAgo")
    end = request.args.get("end", "today")

    client = get_client()
    req = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="eventName"), Dimension(name="date")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date=start, end_date=end)],
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

    response = client.run_report(req)

    dados = {}
    for row in response.rows:
        evento = row.dimension_values[0].value
        data = row.dimension_values[1].value  # YYYYMMDD
        contagem = int(row.metric_values[0].value)
        data_iso = f"{data[0:4]}-{data[4:6]}-{data[6:8]}"
        data_fmt = f"{data[6:8]}/{data[4:6]}/{data[0:4]}"
        if evento not in dados:
            dados[evento] = {}
        dados[evento][data_iso] = {"fmt": data_fmt, "count": contagem}

    totais = {e: sum(v["count"] for v in dados.get(e, {}).values()) for e in EVENTOS}

    todas_datas = sorted(set(
        d for e in dados.values() for d in e.keys()
    ), reverse=True)

    tabela = []
    for data_iso in todas_datas:
        tabela.append({
            "data_iso": data_iso,
            "data": dados.get("page_view", dados.get(EVENTOS[0], {})).get(data_iso, {}).get("fmt", data_iso),
            "whatsapp_click": dados.get("whatsapp_click", {}).get(data_iso, {}).get("count", 0),
            "click_ligar": dados.get("click_ligar", {}).get(data_iso, {}).get("count", 0),
            "scroll_depth": dados.get("scroll_depth", {}).get(data_iso, {}).get("count", 0),
            "tempo_30s_pagina": dados.get("tempo_30s_pagina", {}).get(data_iso, {}).get("count", 0),
            "page_view": dados.get("page_view", {}).get(data_iso, {}).get("count", 0),
        })

    # fix: get fmt from any event that has the date
    for row in tabela:
        iso = row["data_iso"]
        for e in EVENTOS:
            if iso in dados.get(e, {}):
                row["data"] = dados[e][iso]["fmt"]
                break

    return jsonify({"totais": totais, "tabela": tabela})


if __name__ == "__main__":
    print("Painel GA4 rodando em http://localhost:5000")
    app.run(port=5000, debug=True)
