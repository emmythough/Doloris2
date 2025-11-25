# Environment Variables for Render

Add these to your Render service environment variables:

## Required (Already Set)
```
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://...
SUPABASE_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
TELEGRAM_BOT_TOKEN=...
APP_BASE_URL=https://doloris2.onrender.com
```

## NEW: GitHub Integration (for R.D 2.1)
```
GITHUB_TOKEN=ghp_...
GITHUB_REPO=emmythough/Doloris2
```

### How to Get GitHub Token:

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "Doloris R.D 2.1"
4. Expiration: "No expiration" or "1 year"
5. Scopes: Select:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `write:packages` (if using GitHub Packages)
6. Click "Generate token"
7. Copy the token (starts with `ghp_`)
8. Add to Render environment variables

### Optional: Model Override (when GPT-5 available)
```
GPT_5_NANO_MODEL=gpt-5-nano
GPT_5_MINI_MODEL=gpt-5-mini  
GPT_5_1_MODEL=gpt-5.1
```

For now, these default to:
- GPT_5_NANO_MODEL → gpt-4o-mini
- GPT_5_MINI_MODEL → gpt-4o
- GPT_5_1_MODEL → o1-mini

## After Adding Variables

In Render dashboard:
1. Environment tab
2. Add each variable
3. Click "Save Changes"
4. Service will auto-redeploy

⏱️ Takes ~2 minutes to deploy
