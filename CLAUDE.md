# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TfL Weekend Travel Email Summariser — an AWS SAM application that receives TfL's weekend travel advice emails via SES, summarises them using an LLM (moonshotai/kimi-k2.6 via OpenRouter), stores summaries in DynamoDB, and publishes them to a Telegram channel/bot.

## Architecture

Two AWS Lambda functions defined in `template.yaml`:

- **`summarise_tfl_email/`** — Triggered by SES when an email arrives. Reads the email from S3, extracts HTML body, sends to LLM for summarisation, stores result in DynamoDB (`week-id` key format: `YYYY-WW`), and posts to Telegram channel. Supports `dry_run` mode in the event payload to skip storage/publishing. Filters emails by subject using a case-insensitive substring match on `"weekend travel advice"`.
- **`retrieve_summary/`** — HTTP API (via API Gateway). Serves summaries from DynamoDB. Also handles Telegram webhook at `/telegram-webhook` (responds to `/info` command).

LLM backends in `summarise_tfl_email/`:
- `llm_openrouter.py` — Active. Uses OpenRouter API with `moonshotai/kimi-k2.6` model. API key stored in Secrets Manager (`openrouter-api-key`).
- `llm_llama.py` — Legacy/unused. AWS Bedrock with Llama 3.1 70B (`us-west-2` region).
- `llm_palm.py` — Legacy/unused. Google Vertex AI PaLM integration.

External services: AWS S3, DynamoDB, Secrets Manager, OpenRouter API; Telegram Bot API.

## Commands

```bash
SAM_CLI_BETA_UV_PACKAGE_MANAGER=1 sam build   # Build Lambda functions (uv, experimental)
sam deploy             # Deploy to AWS (uses samconfig.toml defaults)
sam validate           # Validate template
sam local invoke SummariseTflEmailFunction -e event.json  # Test locally

# Dry-run the deployed Lambda against the most recent S3 email (no storage/publishing)
uv run --with boto3 python3 dry_run.py
uv run --with boto3 python3 dry_run.py <message-id>  # specify a particular email
```

Dependencies are managed with uv (`pyproject.toml` + `uv.lock` in each function directory).
To add/update dependencies: edit `pyproject.toml` and run `uv lock` in the function directory.

## Key Details

- Python 3.12 runtime, x86_64 architecture
- Region: `eu-west-1` for main stack and OpenRouter secret
- DynamoDB table uses `week-id` (string, `YYYY-WW` format) as partition key with TTL on `ttl` attribute
- Telegram messages are truncated to 4096 chars (Telegram API limit)
- Summaries are converted from Markdown to HTML for Telegram, with unsupported HTML tags stripped
- Telegram credentials (bot token, channel ID, webhook validation token) stored in AWS Secrets Manager
- OpenRouter API key stored in Secrets Manager as `{"api_key": "sk-or-..."}` under secret name `openrouter-api-key`
