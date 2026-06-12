/**
 * App configuration — edit these two values before running.
 *
 * During local testing (phone on same WiFi as your computer):
 *   API_URL = "http://192.168.x.x:8000"   ← your computer's LAN IP
 *   WS_URL  = "ws://192.168.x.x:8000"
 *
 * After deploying to Railway / Render:
 *   API_URL = "https://your-app.railway.app"
 *   WS_URL  = "wss://your-app.railway.app"
 *
 * APP_TOKEN must match APP_SECRET_TOKEN in your server's .env
 */

export const API_URL = 'http://localhost:8000';
export const WS_URL  = 'ws://localhost:8000';
export const APP_TOKEN = 'CHANGE-ME';
