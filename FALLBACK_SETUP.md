# LLM Fallback Setup Guide

Your app now supports **multiple free LLM providers** with automatic fallback!

## Setup Options (in priority order):

### 1️⃣ **PRIMARY: Google Gemini** (Required)
- Already have this setup
- Free tier has rate limits (you hit them)

### 2️⃣ **FALLBACK #1: Groq** (🎯 Recommended - Completely FREE)
- **FREE generous quota!** (14,000 RPM, unlimited requests)
- Super fast inference
- Setup: 2 minutes

**Steps:**
```bash
1. Go to: https://console.groq.com
2. Sign up (free)
3. Get your API key
4. Add to .env: GROQ_API_KEY=your_key_here
```

### 3️⃣ **FALLBACK #2: Ollama** (Completely LOCAL & FREE)
- Runs entirely on your machine
- No API keys needed
- No quota limits
- Slower than cloud APIs

**Steps:**
```bash
1. Download from: https://ollama.ai
2. Install & run: ollama serve
3. In another terminal: ollama pull mistral
4. OLLAMA_BASE_URL is already set to http://localhost:11434
```

### 4️⃣ **FALLBACK #3: OpenAI** (Has quota issues - not recommended)
- Only try this if Groq doesn't work
- Requires paid account ($5+ credits)

## How It Works:
```
API Call Flow:
1. Try Google Gemini (primary)
   ↓ (if quota exceeded or error)
2. Try Groq (fastest free option)
   ↓ (if Groq fails or no key)
3. Try Ollama (local, runs on your machine)
   ↓ (if Ollama not running or no key)
4. Try OpenAI (if configured)
```

## Quick Start:

### Option A: Just use Groq (Easiest - 2 min)
```bash
# 1. Get free Groq key: https://console.groq.com
# 2. Add to .env:
GROQ_API_KEY=your_groq_key

# 3. Run
streamlit run app.py
```

### Option B: Use Ollama (No costs, works offline)
```bash
# 1. Download & install: https://ollama.ai
# 2. In terminal 1: ollama serve
# 3. In terminal 2: ollama pull mistral
# 4. OLLAMA_BASE_URL=http://localhost:11434 (already in config)

# 5. Run
streamlit run app.py
```

### Option C: Use Both Groq + Ollama (Most Robust)
- Get Groq key (fast, cloud-based fallback)
- Setup Ollama locally (ultimate fallback)
- App will try both automatically

## Test It:
```bash
# Just run the app
streamlit run app.py

# Check logs to see which provider is being used
# You'll see messages like:
# "🔄 Switching to Groq (Mixtral-8x7b) fallback..."
# "🔄 Switching to Ollama (mistral) fallback..."
```

## Troubleshooting:

**"Groq API key not configured"?**
- Add `GROQ_API_KEY=your_key` to `.env`

**"Ollama not running"?**
- Run: `ollama serve` in a new terminal

**All fallbacks failing?**
- Check that at least ONE of these is configured:
  - GROQ_API_KEY (easiest)
  - Ollama running on http://localhost:11434
  - OPENAI_API_KEY (requires paid account)

## Estimated Costs:
- **Google Gemini Free Tier**: FREE (but limited)
- **Groq Free Tier**: FREE (very generous!)
- **Ollama**: FREE (100% local, no internet needed)
- **OpenAI**: ~$0.0005 per request (NOT recommended)

## Recommendation:
**Go with Groq!** It's free, fast, and requires only a 2-minute signup. If you want complete offline capability, also setup Ollama as a backup.
