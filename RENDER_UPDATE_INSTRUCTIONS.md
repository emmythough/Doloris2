# URGENT: Update Render Environment Variables

## The Problem
Your bot receives messages (200 OK) but doesn't respond because Render is using the OLD token.

## The Fix (2 minutes)

### Step 1: Go to Render Dashboard
1. Open: https://dashboard.render.com/
2. Click on your `doloris2` service

### Step 2: Update Environment Variables
1. Click the **"Environment"** tab on the left
2. Find `TELEGRAM_BOT_TOKEN`
3. Click **Edit** (pencil icon)
4. Replace with your new token from BotFather
5. Click **Save Changes**

### Step 3: Wait for Redeploy
- Render will automatically redeploy (takes ~2 minutes)
- Watch the "Events" tab for "Deploy succeeded"

### Step 4: Test Again
- Message @doloris2_bot in Telegram
- You should get a response!

---

## Alternative: Manual Deploy via Render Dashboard
If auto-deploy is off:
1. Go to your service page
2. Click **Manual Deploy** → **Deploy latest commit**
3. Wait for deployment to complete
4. Test the bot

---

## Need Help?
If you want me to verify the deployment, share the Render logs after the redeploy.
