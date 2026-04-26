# Render Deployment Fix

The issue you encountered ("This site can't be reached" at localhost:8000) was caused by a hardcoded redirect URI in the OAuth configuration.

## What was fixed in the code:

1.  **Dynamic Redirect URI**: Modified `app/core/config.py` to derive the `GOOGLE_REDIRECT_URI` from a new `BASE_URL` setting.
2.  **Proxy Header Support**: Added `ProxyHeadersMiddleware` to `app/main.py` so the app correctly handles HTTPS on Render.

## Steps you need to take:

1.  **Render Dashboard**:
    *   Go to your Web Service **Environment** settings.
    *   Add `BASE_URL`: `https://your-app-name.onrender.com`
2.  **Google Cloud Console**:
    *   Add `https://your-app-name.onrender.com/auth/google/callback` to your **Authorized redirect URIs**.

The app is now ready for production!
