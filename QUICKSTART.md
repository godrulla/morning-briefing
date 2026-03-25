# Quick Start Guide

Get your morning briefing running in 15 minutes!

## Step 1: Run Setup (2 minutes)

```bash
cd ~/Documents/morning-briefing
./setup.sh
```

## Step 2: Get Google Credentials (5 minutes)

1. Go to https://console.cloud.google.com
2. Create project → Enable Gmail API & Calendar API
3. Create OAuth credentials (Desktop app)
4. Download `credentials.json`
5. Move to: `~/Documents/morning-briefing/credentials/credentials.json`

## Step 3: Get GitHub Token (2 minutes)

1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select: `repo`, `read:user`, `read:org`
4. Copy token

## Step 4: Configure (3 minutes)

Edit `config.yaml`:
```yaml
user:
  email: "your@email.com"

github:
  username: "your-username"
```

Edit `secrets.yaml`:
```yaml
github:
  access_token: "ghp_YOUR_TOKEN_HERE"
```

## Step 5: Test (3 minutes)

```bash
./test.sh --dry-run    # Test without sending email
./test.sh              # Send real test email
```

## Done! 🎉

Your briefing will arrive every morning at 7:00 AM!

### Quick Commands

```bash
./test.sh --dry-run                        # Test without email
launchctl start com.exxede.morning-briefing  # Run now
tail -f ~/.local/logs/morning-briefing.log   # View logs
```

### Need Help?

Check `README.md` for full documentation.
