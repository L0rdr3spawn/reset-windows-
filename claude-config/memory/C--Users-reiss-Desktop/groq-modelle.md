---
name: groq-modelle
description: "Which models the user's Groq account offers (screenshot 2026-10-06) and which ones ask-cheap uses"
metadata:
  node_type: memory
  type: reference
  originSessionId: 1c24c93e-6711-4fd0-8614-56213b64a182
  modified: 2026-10-06T14:14:34.093Z
---

Groq "Base Models" list in the user's console (2026-10-06):
- LLMs (text): `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`
- Speech-to-text: `whisper-large-v3`, `whisper-large-v3-turbo`
- TTS: `canopylabs/orpheus-v1-english`, `canopylabs/orpheus-arabic-saudi`
- Safety classifiers (not for chat): `meta-llama/llama-prompt-guard-2-22m`, `-86m`, `openai/gpt-oss-safeguard-20b`

No llama-3.x chat models anymore. [[ask-cheap]] uses gpt-oss-120b (default), gpt-oss-20b (--fast), qwen3.8-27b (fallback).
User prefers local dictation (Handy), so don't push Groq whisper for that.
