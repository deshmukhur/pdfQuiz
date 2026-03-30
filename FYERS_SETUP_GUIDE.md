# Fyers API Setup Guide (Step-by-Step for Beginners)

This guide walks you through setting up the Fyers API from scratch so the Stock Market Analysis Platform can receive real-time market data.

---

## What You Need

- A **Fyers trading account** (if you don't have one, sign up at [https://fyers.in](https://fyers.in))
- A **Fyers API app** (free to create — instructions below)

---

## Step 1: Create a Fyers API App

1. Go to **[https://myapi.fyers.in/dashboard](https://myapi.fyers.in/dashboard)**
2. Log in with your Fyers trading credentials
3. Click **"Create App"** (or **"+ New App"**)
4. Fill in the form:
   - **App Name:** `StockScanner` (or any name you like)
   - **Redirect URL:** `http://127.0.0.1:8000/api/auth/fyers/callback`
     - **This is important!** This URL tells Fyers where to send you back after login. Our backend has a page at this exact URL that will catch the login response and save your token.
   - **App Type:** Select `Web`
   - **Description:** `Stock market analysis platform` (optional)
5. Click **"Create"**

After creation, you'll see:
- **App ID** (also called Client ID) — looks like `XXXXXXXX-100`
- **Secret Key** — a string of characters

**Save both of these!** You'll need them in Step 2.

---

## Step 2: Put Your Credentials in the .env File

1. Open the file `backend/.env` in any text editor
2. Update these three lines with your values:

```
FYERS_CLIENT_ID=YOUR_APP_ID_HERE
FYERS_SECRET=YOUR_SECRET_KEY_HERE
FYERS_REDIRECT_URI=http://127.0.0.1:8000/api/auth/fyers/callback
```

For example, if your App ID is `ABC123XYZ-100` and secret is `MYSECRET456`:
```
FYERS_CLIENT_ID=ABC123XYZ-100
FYERS_SECRET=MYSECRET456
FYERS_REDIRECT_URI=http://127.0.0.1:8000/api/auth/fyers/callback
```

3. Save the file

---

## Step 3: Start the Application

```bash
# Linux/Mac
chmod +x start.sh
./start.sh

# Windows
start.bat
```

Wait until you see:
```
Both servers are running!
Dashboard:  http://localhost:4200
```

---

## Step 4: Authenticate with Fyers

### Option A: OAuth Login (Recommended)

1. Open your browser and go to **http://localhost:4200/auth**
2. You'll see the **"Fyers API Authentication"** page showing "Not Connected"
3. Click **"Login with Fyers"**
4. A new browser tab/window opens with the Fyers login page
5. Enter your **Fyers trading credentials** (the same ones you use to log into Fyers web/app)
6. After successful login, Fyers redirects you back to `http://127.0.0.1:8000/api/auth/fyers/callback`
7. You'll see a JSON response saying `"Authentication successful. Token stored."`
8. Go back to the **Auth page** (http://localhost:4200/auth) and click **"Refresh Status"**
9. It should now show **"Connected"** in green

### Option B: Manual Token (If OAuth doesn't work)

If the redirect doesn't work or you already have an access token, you can paste it manually:

1. **Get a token using Python** (run this in a terminal):
```python
from fyers_apiv3 import fyersModel

session = fyersModel.SessionModel(
    client_id="YOUR_APP_ID",      # e.g. "ABC123XYZ-100"
    secret_key="YOUR_SECRET",     # e.g. "MYSECRET456"
    redirect_uri="http://127.0.0.1:8000/api/auth/fyers/callback",
    response_type="code",
    grant_type="authorization_code",
)

# This prints a URL — open it in your browser
print(session.generate_authcode())
```

2. Open the printed URL in your browser
3. Log in with Fyers credentials
4. After login, you'll be redirected to a URL like:
   ```
   http://127.0.0.1:8000/api/auth/fyers/callback?auth_code=eyJ0eXAi...&s=ok
   ```
5. Copy the `auth_code` value from the URL (the long string starting with `eyJ0eXAi...`)
6. Now exchange it for an access token:

```python
session.set_token("PASTE_AUTH_CODE_HERE")
response = session.generate_token()
print(response)
# Response: {'s': 'ok', 'code': 200, 'access_token': 'eyJ0eXAi...', ...}
```

7. Copy the `access_token` value
8. Go to **http://localhost:4200/auth**
9. Paste the token in the **"Access Token"** field
10. Click **"Set Token"**
11. Status should change to **"Connected"**

---

## What is the Redirect URL?

**Simple explanation:** When you click "Login with Fyers", the app sends you to the Fyers website to log in. After you log in successfully, Fyers needs to know where to send you back. The **Redirect URL** is that "send back" address.

In our case, the Redirect URL is:
```
http://127.0.0.1:8000/api/auth/fyers/callback
```

This points to a page on your local backend server that:
1. Receives the authorization code from Fyers
2. Exchanges it for an access token
3. Stores the token so the scanner can use it

**Important:** The Redirect URL in your Fyers app settings MUST match exactly what's in your `.env` file. If they don't match, authentication will fail.

---

## Step 5: Verify It's Working

Once authenticated:

1. Go to **http://localhost:4200/dashboard**
2. During market hours (09:15–15:30 IST, Mon–Fri), you should see:
   - The scanner running every 60 seconds
   - Instruments appearing in the table with scores and signals
   - Real-time price updates
3. Outside market hours, the scanner won't produce data, but you can:
   - Check the **News** page for fetched articles
   - Check the **Auth** page to confirm connection status
   - View the **API Docs** at http://localhost:8000/docs

---

## Troubleshooting

### "Login with Fyers" opens but login fails
- Double-check your `FYERS_CLIENT_ID` and `FYERS_SECRET` in `.env`
- Make sure the Redirect URL in your Fyers API dashboard matches exactly: `http://127.0.0.1:8000/api/auth/fyers/callback`

### Redirect page shows an error
- Make sure the backend is running (check http://localhost:8000/health)
- The redirect URL must use `127.0.0.1` not `localhost` — they are treated differently by Fyers

### "Not Connected" after login
- Click **"Refresh Status"** on the Auth page
- Check the backend terminal for any error messages
- Try the manual token method (Option B above)

### No data in the dashboard
- The scanner only runs during **market hours** (09:15–15:30 IST, Mon–Fri)
- Make sure Fyers is authenticated (check Auth page)
- Check backend logs: look at the terminal where you ran `start.sh`

### Backend keeps restarting
- This was a known issue in v1 — the updated `start.sh` fixes it by excluding the `venv/` folder from file watching
- Re-download the latest zip if you're using an older version

---

## Token Expiry

- Fyers access tokens **expire daily** (usually at end of day or after ~24 hours)
- You'll need to re-authenticate each trading day
- Simply go to the Auth page and click "Login with Fyers" again
- There is also a refresh token mechanism — see Fyers API docs for details

---

## Summary

| Step | Action |
|------|--------|
| 1 | Create an app at [myapi.fyers.in](https://myapi.fyers.in/dashboard) |
| 2 | Put App ID + Secret in `backend/.env` |
| 3 | Run `./start.sh` (or `start.bat`) |
| 4 | Go to http://localhost:4200/auth and click "Login with Fyers" |
| 5 | Log in with your Fyers trading credentials |
| 6 | Dashboard auto-populates during market hours |
