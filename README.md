# Relatórios VSL — Storage & Relay

Repo intermediário entre a **Cloud Routine** (Anthropic) e o **site Vercel + WhatsApp**.

## Por que existe

A Cloud Routine roda em sandbox com TLS inspection que bloqueia chamadas pra `*.vercel.app` e hosts arbitrários. Mas `github.com` está na allowlist. Solução: a Cloud Routine commita arquivos JSON aqui, e o GitHub Actions (que tem internet livre) faz o forward pro Vercel + WhatsApp.

## Fluxo

```
Cloud Routine (sandbox)
  ↓ git push relatorios/YYYY-MM-DD.json
GitHub repo (este)
  ↓ trigger workflow
GitHub Action (.github/workflows/relay.yml)
  ↓ POST → relatorios-vsl.vercel.app/api/ingest
  ↓ POST → whatsapp-relay.vercel.app/api/relay
Site público + WhatsApp grupo
```

## Estrutura

```
relatorios/
  2026-05-03.json   ← cada arquivo = 1 relatório do dia
  ...

.github/workflows/
  relay.yml         ← workflow que processa novos arquivos
```

## Schema do JSON (cada relatório)

```json
{
  "date": "YYYY-MM-DD",
  "summary": {
    "roas": 1.57,
    "revenue": 2441.14,
    "spend": 1559.46,
    "profit": 881.68,
    "vendas": 9,
    "cpa": 173.27,
    "ctr": 1.20,
    "conv_checkout": 12.7,
    "conv_pagina_venda": 1.21
  },
  "destaque": "ADS112 TERAPEUTA 02 — ROAS 6,03×",
  "atencao": "F22 em prejuízo há 5 dias",
  "acao_prioritaria": "Matar F22 e escalar ADS112 +30%",
  "alerta_critico": null,
  "markdown": "# Relatório Diário VSL... (markdown completo com 9 seções)"
}
```

## Secrets necessários (GitHub Actions)

| Nome | Valor |
|---|---|
| `RELAY_SECRET` | Token compartilhado com Vercel |
| `INGEST_URL` | https://relatorios-vsl.vercel.app/api/ingest |
| `WHATSAPP_RELAY_URL` | https://whatsapp-relay.vercel.app/api/relay |
| `WHATSAPP_GROUP_JID` | 120363409136699753@g.us |

## Disparo manual

Via GitHub UI: **Actions** → **Relay relatório → Vercel + WhatsApp** → **Run workflow** → preencher caminho do arquivo.
