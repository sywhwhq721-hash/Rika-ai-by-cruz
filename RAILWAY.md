# Railway Deployment Configuration

This bot is configured to run on Railway platform.

## Environment Variables Required

Add these environment variables in your Railway project:

```env
BOT_TOKEN=8628786630:AAENaSvViSaK_WinoYxHaXmsR5lvcFzdLWk
API_ID=38081166
API_HASH=f608a6dcf2b1d4761c53ff29d00c5bbf
MONGO_URI=mongodb+srv://Lucifer:<Lucky1976208>@cluster0.9lfbgac.mongodb.net/?appName=Cluster0
LOG_CHAT_ID=-1004315457394
OWNER_ID=8705127026
```

## Deployment Steps

1. Connect your GitHub repository to Railway
2. Add the environment variables from the `.env` template
3. Deploy using the Procfile configuration
4. Monitor logs from Railway dashboard

## Features

- ✅ Long polling support
- ✅ Environment variable management
- ✅ MongoDB integration
- ✅ Proper error handling and cleanup
- ✅ Auto-restart on failure

## Logs

Check Railway logs to monitor bot activity and debug issues.
