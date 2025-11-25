# Debugging Guide for Doloris 2.0

## 🔍 Overview

This guide helps you diagnose issues with Telegram message processing using the enhanced debugging features and Render CLI integration.

---

## 🚀 Quick Start - Setup Render CLI

### Step 1: Setup the CLI

```bash
python setup_render_cli.py
```

This will verify that `cli_v1.1.0.exe` is present and create a convenient wrapper.

### Step 2: Login to Render

```bash
cli_v1.1.0.exe login
```

Or if the wrapper was created:

```bash
render login
```

This opens a browser for authentication.

---

## 📊 Monitoring Logs

### Real-time Log Monitoring

Watch all logs in real-time:

```bash
python monitor_logs.py
```

### Filter for Specific Patterns

Watch only webhook-related logs:

```bash
python monitor_logs.py --filter WEBHOOK
```

Watch only errors:

```bash
python monitor_logs.py --filter ERROR
```

Watch adapter logs:

```bash
python monitor_logs.py --filter ADAPTER
```

Watch brain logs:

```bash
python monitor_logs.py --filter BRAIN
```

### View Recent Logs

Get the last 100 log lines:

```bash
python monitor_logs.py --recent 100
```

Get the last 500 lines:

```bash
python monitor_logs.py --recent 500
```

---

## 🧪 Testing Without Telegram

### Test the Message Flow Directly

Test with a specific user ID:

```bash
curl -X POST "https://your-app.onrender.com/diagnostic/test-message?user_id=YOUR_TELEGRAM_ID&text=Hello"
```

### Test with Sample Webhook Payload

```bash
curl -X POST "https://your-app.onrender.com/diagnostic/test-webhook"
```

This simulates a complete Telegram webhook payload.

### Detailed Health Check

```bash
curl "https://your-app.onrender.com/diagnostic/health-detailed"
```

This checks:
- Database connectivity
- OpenAI API configuration
- Telegram bot token configuration

---

## 🔎 Understanding the Logs

### Log Prefixes

The enhanced logging uses these prefixes:

- **`[WEBHOOK:req_XXX]`** - Webhook handler (main entry point)
- **`[ADAPTER]`** - Telegram adapter (processes updates, sends messages)
- **`[BRAIN]`** - Brain orchestrator (handles AI logic)

### Request Tracking

Each webhook request gets a unique ID like `req_1234567890`. You can trace a single request through all components by searching for this ID.

Example log flow for a successful message:

```
[WEBHOOK:req_123] ====== NEW REQUEST ======
[WEBHOOK:req_123] 📥 RAW TELEGRAM PAYLOAD: {...}
[WEBHOOK:req_123] 📋 MESSAGE INFO: {"text": "Hello", ...}
[WEBHOOK:req_123] 🔄 STEP 1/4: Processing update via TelegramAdapter...
[ADAPTER] 🔍 Starting update processing...
[ADAPTER] 👤 Extracted user_id: 123456789
[ADAPTER] 💬 Text: 'Hello', Caption: ''
[ADAPTER] ✅ Processing complete: user_id=123456789, text_len=5, has_file=False
[WEBHOOK:req_123] ⏱️ Adapter processing took 0.05s
[WEBHOOK:req_123] 🧠 STEP 2/4: Sending to Brain for processing...
[BRAIN] 🧠 Processing message from user 123456789: 'Hello'...
[BRAIN] ✅ Got response: 'Hello! How can I help you?'
[WEBHOOK:req_123] ⏱️ Brain processing took 2.34s
[WEBHOOK:req_123] 📤 STEP 3/4: Sending response to chat_id=123456789
[ADAPTER] 📤 Sending message to chat_id=123456789
[ADAPTER] ✅ Message sent successfully!
[WEBHOOK:req_123] ⏱️ TOTAL TIME: 2.45s
[WEBHOOK:req_123] ====== REQUEST COMPLETE ======
```

### Error Detection

Errors are clearly marked:

```
[WEBHOOK:req_123] ❌ ====== ERROR ======
[WEBHOOK:req_123] ❌ ERROR TYPE: KeyError
[WEBHOOK:req_123] ❌ ERROR MESSAGE: 'message'
[WEBHOOK:req_123] ❌ FULL TRACEBACK:
...
[WEBHOOK:req_123] ====== ERROR END ======
```

---

## 🛠️ Common Issues & Solutions

### Issue: "Nothing happens when I send a message"

**Diagnosis Steps:**

1. **Check if webhook is receiving messages:**
   ```bash
   python monitor_logs.py --filter WEBHOOK
   ```
   
   Then send a test message to your bot. You should see:
   ```
   [WEBHOOK:req_XXX] ====== NEW REQUEST ======
   ```

   ❌ **If you see nothing:** Telegram isn't reaching your webhook
   - Verify webhook is set correctly: `python set_webhook.py`
   - Check Render service is running
   - Verify `TELEGRAM_BOT_TOKEN` environment variable in Render

   ✅ **If you see the log:** Webhook is working, continue to next step

2. **Check adapter processing:**
   ```bash
   python monitor_logs.py --filter ADAPTER
   ```
   
   Look for:
   ```
   [ADAPTER] 👤 Extracted user_id: 123456789
   ```

   ❌ **If user_id is None:** Payload format issue
   - Check the RAW TELEGRAM PAYLOAD in logs
   - Verify Telegram is sending proper format

3. **Check brain processing:**
   ```bash
   python monitor_logs.py --filter BRAIN
   ```
   
   Look for errors in OpenAI calls or database queries.

4. **Check message sending:**
   Look for:
   ```
   [ADAPTER] ✅ Message sent successfully!
   ```

   ❌ **If you see error:** Check bot token is correct

### Issue: "Slow response times"

Check the timing logs:

```
[WEBHOOK:req_123] ⏱️ Adapter processing took 0.05s
[WEBHOOK:req_123] ⏱️ Brain processing took 5.34s  ← SLOW!
[WEBHOOK:req_123] ⏱️ Message send took 0.12s
[WEBHOOK:req_123] ⏱️ TOTAL TIME: 5.51s
```

This shows the brain (OpenAI call) is the bottleneck.

### Issue: "Bot responds with error message"

Check for:
```
[BRAIN] ❌ ERROR: ...
```

This will show the exact error and traceback.

---

## 📝 Example Debugging Session

**Problem:** User reports bot not responding

**Step 1:** Monitor logs while sending a test message

```bash
python monitor_logs.py --filter WEBHOOK
```

Send message to bot...

**Step 2:** Analyze what you see

**Scenario A - Nothing appears:**
- Webhook not set or not reaching your server
- Check Render deployment status
- Re-run `python set_webhook.py`

**Scenario B - Request appears but error:**
```
[WEBHOOK:req_123] ❌ ERROR TYPE: HTTPException
```
- Look at the full traceback
- Common causes: Database connection, OpenAI API key

**Scenario C - Request completes but no message sent:**
```
[ADAPTER] ❌ Failed to send message: 401
```
- Wrong bot token
- Check `TELEGRAM_BOT_TOKEN` in Render environment variables

---

## 🎯 Pro Tips

1. **Use request IDs:** When reporting issues, copy the request ID (`req_XXX`) to track a specific message

2. **Check multiple log sources:**
   - Webhook logs show the entry point
   - Adapter logs show Telegram communication
   - Brain logs show AI processing

3. **Test locally first:**
   Use the diagnostic endpoints to test without Telegram:
   ```bash
   curl -X POST "http://localhost:8000/diagnostic/test-message?user_id=123&text=Test"
   ```

4. **Filter aggressively:**
   When diagnosing, use specific filters to reduce noise:
   ```bash
   python monitor_logs.py --filter "ERROR"
   python monitor_logs.py --filter "req_123456"
   ```

---

## 📚 Reference

### Log Levels

- **INFO** (ℹ️): Normal operation
- **WARNING** (⚠️): Potential issues
- **ERROR** (❌): Actual errors
- **DEBUG** (🔍): Detailed debugging info

### Key Files

- `app/telegram_webhook.py` - Webhook handler with request tracking
- `app/channels/telegram_adapter.py` - Telegram message processing
- `app/core/brain.py` - AI orchestration
- `monitor_logs.py` - Log monitoring tool
- `setup_render_cli.py` - CLI setup

### Useful Commands

```bash
# Setup
python setup_render_cli.py
cli_v1.1.0.exe login

# Monitor
python monitor_logs.py
python monitor_logs.py --filter WEBHOOK
python monitor_logs.py --recent 200

# Test
curl -X POST "https://your-app.onrender.com/diagnostic/test-message?user_id=123&text=Hi"
curl "https://your-app.onrender.com/diagnostic/health-detailed"
```

---

## 🆘 Still Stuck?

If you're still having issues:

1. Capture the full request ID and logs
2. Run the detailed health check
3. Test with diagnostic endpoint
4. Share the specific error messages

The enhanced logging should give you visibility into exactly where the message flow breaks down!
