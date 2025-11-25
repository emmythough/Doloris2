# 🚀 Quick Start - Debugging Doloris 2.0

## You sent a message but bot didn't respond? Here's how to find out why:

### Option 1: Monitor Logs (Recommended)

1. **Setup Render CLI** (one-time):
   ```bash
   python setup_render_cli.py
   cli_v1.1.0.exe login
   ```

2. **Watch logs in real-time**:
   ```bash
   python monitor_logs.py --filter WEBHOOK
   ```

3. **Send a test message** to your bot

4. **Watch what happens** in the logs:
   - ✅ See request coming in? → Webhook is working
   - ❌ Nothing? → Webhook not set or token wrong
   - 🔴 Error? → Check the error message

### Option 2: Test Directly (No Telegram needed)

Test the flow without Telegram:

```bash
curl -X POST "https://doloris2.onrender.com/diagnostic/test-message?user_id=YOUR_TELEGRAM_ID&text=Hello"
```

Replace `YOUR_TELEGRAM_ID` with your actual Telegram user ID.

### Option 3: Health Check

```bash
curl "https://doloris2.onrender.com/diagnostic/health-detailed"
```

This checks if:
- ✅ Database is connected
- ✅ OpenAI API key is set
- ✅ Telegram bot token is configured

---

## Common Fixes

### "Nothing happens"
1. Check webhook: `python set_webhook.py`
2. Verify bot token in Render environment variables
3. Check if service is running on Render dashboard

### "Bot responds but very slow"
- Check logs for timing:
  ```bash
  python monitor_logs.py --filter "⏱️"
  ```
- OpenAI calls can take 2-5 seconds (this is normal)

### "Error in logs"
- Copy the full error from logs
- Check `DEBUGGING_GUIDE.md` for solution
- Most errors are from:
  - Missing environment variables
  - Database connection issues
  - OpenAI API issues

---

## Need More Help?

See **`DEBUGGING_GUIDE.md`** for the complete troubleshooting guide.

---

## What Changed?

The codebase now has **extensive logging** that shows:
- Every incoming Telegram message (full payload)
- How long each step takes
- Exactly where errors occur
- Request tracking with unique IDs

You can now see **exactly** what's happening instead of guessing!
