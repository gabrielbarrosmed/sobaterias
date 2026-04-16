"""
Analisa campanhas Google Ads: performance dos últimos 30 dias.
Execute: python tools/analyze_campaigns.py
"""
import os
import sys
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

YAML_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "google-ads.yaml")

def format_currency(micros):
    return f"R$ {micros / 1_000_000:.2f}"

def main():
    client = GoogleAdsClient.load_from_storage(YAML_PATH)
    ga_service = client.get_service("GoogleAdsService")
    customer_id = "6771795003"  # SÓ BATERIAS (conta filha real)

    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.ctr,
            metrics.average_cpc,
            metrics.search_impression_share
        FROM campaign
        WHERE segments.date DURING LAST_30_DAYS
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """

    try:
        response = ga_service.search_stream(customer_id=str(customer_id), query=query)

        campaigns = []
        for batch in response:
            for row in batch.results:
                m = row.metrics
                c = row.campaign
                campaigns.append({
                    "id": c.id,
                    "name": c.name,
                    "status": c.status.name,
                    "channel": c.advertising_channel_type.name,
                    "impressions": m.impressions,
                    "clicks": m.clicks,
                    "cost": m.cost_micros,
                    "conversions": m.conversions,
                    "conv_value": m.conversions_value,
                    "ctr": m.ctr * 100,
                    "avg_cpc": m.average_cpc,
                    "impression_share": m.search_impression_share,
                })

        if not campaigns:
            print("Nenhuma campanha encontrada nos últimos 30 dias.")
            return

        print(f"\n{'='*70}")
        print(f"ANÁLISE DE CAMPANHAS GOOGLE ADS — Últimos 30 dias")
        print(f"Customer ID: {customer_id}")
        print(f"{'='*70}\n")

        total_cost = sum(c["cost"] for c in campaigns)
        total_clicks = sum(c["clicks"] for c in campaigns)
        total_impressions = sum(c["impressions"] for c in campaigns)
        total_conversions = sum(c["conversions"] for c in campaigns)

        print(f"RESUMO GERAL")
        print(f"  Gasto total:      {format_currency(total_cost)}")
        print(f"  Impressões:       {total_impressions:,}")
        print(f"  Cliques:          {total_clicks:,}")
        print(f"  CTR médio:        {(total_clicks/total_impressions*100) if total_impressions else 0:.2f}%")
        print(f"  CPC médio:        {format_currency(total_cost/total_clicks) if total_clicks else 0}")
        print(f"  Conversões:       {total_conversions:.1f}")
        cpa = total_cost / 1_000_000 / total_conversions if total_conversions else 0
        print(f"  CPA:              R$ {cpa:.2f}")
        print(f"\n{'─'*70}")

        print(f"\nDETALHE POR CAMPANHA\n")
        for c in campaigns:
            status_icon = "✓" if c["status"] == "ENABLED" else "⏸"
            print(f"  {status_icon} {c['name']}")
            print(f"     Canal: {c['channel']}  |  Status: {c['status']}")
            print(f"     Gasto:       {format_currency(c['cost'])}")
            print(f"     Impressões:  {c['impressions']:,}  |  Cliques: {c['clicks']:,}  |  CTR: {c['ctr']:.2f}%")
            print(f"     CPC médio:   {format_currency(c['avg_cpc'])}")
            print(f"     Conversões:  {c['conversions']:.1f}")
            if c["impression_share"] and c["impression_share"] > 0:
                print(f"     Imp. Share:  {c['impression_share']*100:.1f}%")
            print()

    except GoogleAdsException as ex:
        print(f"Erro Google Ads API: {ex.error.code().name}")
        for error in ex.failure.errors:
            print(f"  {error.message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
