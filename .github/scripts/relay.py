#!/usr/bin/env python3
"""Lê arquivos JSON de relatorios/ e faz forward pro Vercel + WhatsApp."""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

RELAY_SECRET = os.environ["RELAY_SECRET"]
INGEST_URL = os.environ["INGEST_URL"]
WHATSAPP_RELAY_URL = os.environ["WHATSAPP_RELAY_URL"]
WHATSAPP_GROUP_JID = os.environ["WHATSAPP_GROUP_JID"]
FILES = os.environ.get("FILES", "").strip()
REPORT_BASE_URL = "https://relatorios-vsl.vercel.app/r"


def post(url: str, payload: dict, secret: str | None = None) -> tuple[int, dict]:
    headers = {"Content-Type": "application/json"}
    if secret:
        headers["x-relay-token"] = secret
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()}
    except Exception as e:
        return 0, {"error": str(e)}


def fmt_brl(v) -> str:
    if v is None:
        return "—"
    s = f"R$ {v:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_date_br(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"


def build_message(payload: dict, report_url: str) -> str:
    s = payload.get("summary", {})
    date_br = fmt_date_br(payload["date"])
    hora = datetime.now(timezone(timedelta(hours=-3))).strftime("%H:%M")

    roas = s.get("roas")
    roas_str = f"{roas:.2f}".replace(".", ",") if roas is not None else "—"

    msg = f"""📊 *Relatório VSL — {date_br}*

💰 *Faturamento líq:* {fmt_brl(s.get('revenue'))}
💸 *Investimento:* {fmt_brl(s.get('spend'))}
📈 *ROAS:* {roas_str}×
✅ *Lucro:* {fmt_brl(s.get('profit'))}
🛒 *Vendas:* {s.get('vendas', '—')} aprovadas

🏆 *Destaque do dia:*
{payload.get('destaque', '—')}

⚠️ *Atenção:*
{payload.get('atencao', '—')}

🎯 *Ação prioritária HOJE:*
{payload.get('acao_prioritaria', '—')}

📑 Relatório completo:
{report_url}

_Gerado às {hora}_"""

    alerta = payload.get("alerta_critico")
    if alerta:
        msg = f"🚨 *ALERTA CRÍTICO:* {alerta}\n\n" + msg

    return msg


def process_file(filepath: str) -> bool:
    print(f"\n{'='*60}\nProcessando: {filepath}\n{'='*60}")

    if not os.path.isfile(filepath):
        print(f"  ✗ arquivo não existe")
        return False

    with open(filepath) as f:
        payload = json.load(f)

    date = payload.get("date")
    if not date:
        print(f"  ✗ campo 'date' faltando")
        return False

    report_url = f"{REPORT_BASE_URL}/{date}"

    # 1. Publicar no Vercel
    print("\n[1/2] POST /api/ingest no Vercel...")
    code, body = post(INGEST_URL, payload, RELAY_SECRET)
    print(f"  Status: {code}")
    print(f"  Resposta: {json.dumps(body)[:300]}")

    ingest_ok = code == 200

    # 2. Enviar WhatsApp (independente do ingest)
    print("\n[2/2] POST /api/relay WhatsApp...")
    message = build_message(payload, report_url)
    code, body = post(
        WHATSAPP_RELAY_URL,
        {"number": WHATSAPP_GROUP_JID, "text": message},
        RELAY_SECRET,
    )
    print(f"  Status: {code}")
    print(f"  Resposta: {json.dumps(body)[:300]}")

    wa_ok = code == 200

    print(f"\n  Publicação: {'✓' if ingest_ok else '✗'} | WhatsApp: {'✓' if wa_ok else '✗'}")
    print(f"  URL: {report_url}")

    return ingest_ok and wa_ok


def main():
    if not FILES:
        print("Nenhum arquivo pra processar.")
        sys.exit(0)

    files = [f for f in FILES.split() if f.strip()]
    if not files:
        print("Lista de arquivos vazia.")
        sys.exit(0)

    print(f"Arquivos: {files}")

    failed = []
    for f in files:
        ok = process_file(f)
        if not ok:
            failed.append(f)

    if failed:
        print(f"\n❌ Falhou em: {failed}")
        sys.exit(1)
    print(f"\n✅ Tudo certo ({len(files)} arquivo(s))")


if __name__ == "__main__":
    main()
