# Linguistic Error Analyzer

AI-powered Telegram bot for German learners that provides real-time grammar correction, structured error explanations, and builds a dataset of learner mistakes for future analysis.

## What it does

- Corrects German sentences and translates them instantly
- Breaks down mistakes into structured, explainable errors
- Classifies each error by type and CEFR level
- Stores all errors in a database for analytics and future learning features

## Why it matters

Most tools only correct text.  
This project focuses on **understanding mistakes at scale**:

- every error is structured and persisted
- errors are categorized into a consistent taxonomy
- data can be aggregated into statistics and learning insights

This turns a simple bot into a **data collection and analysis pipeline for language learning**.

## Example

<div align="center">
  <img src="assets/demo.gif" alt="Demo of Linguistic Error Analyzer">
</div>

## Architecture & Engineering

### Data persistence (core feature)
All detected errors are stored in a database with structured metadata:
- error type
- CEFR level
- correction pair (original → fixed)

This enables:
- aggregation of common mistakes
- user-level statistics (planned `/stats`)
- foundation for future learning analytics

### Production deployment
- deployed on Hetzner
- CI/CD via GitHub Actions (auto-deploy on merge)
- rate limiting and token control to manage API costs

### Structured LLM output  
Uses OpenAI API + Pydantic to enforce strict JSON schemas and eliminate unreliable parsing.

### Async two-stage pipeline
- fast response: corrected sentence + translation  
- delayed response: detailed error explanations  

Improves UX while handling LLM latency.

### Context-aware analysis
Supports both sentence-level and context-based correction for better handling of:
- agreement
- tense consistency
- multi-sentence dependencies

### Error taxonomy (manually designed)
Each mistake is classified into fine-grained categories:
- grammar (cases, articles, verb forms)
- word order
- vocabulary and collocations
- contextual and register errors

## Tech Stack

- Python, Aiogram
- OpenAI API
- Pydantic
- PostgreSQL / SQLite
- Docker
- GitHub Actions
- Hetzner Cloud

## Roadmap

- `/stats` command for error analytics
- aggregation of most frequent mistake categories
- potential personalized exercises based on stored errors

## Link

https://t.me/satzfix_bot
