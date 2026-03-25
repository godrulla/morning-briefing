# Morning Briefing Automation

Automated daily briefing system that aggregates your calendar, GitHub activity, and important emails into a beautifully formatted morning email.

**Created for:** Armando Diaz Silverio
**Company:** Exxede Investments
**Location:** Punta Cana, Dominican Republic

---

## Features

- **📅 Today's Schedule** - Google Calendar events with priority detection
- **✅ Yesterday's Work** - GitHub commits, merged PRs, and contributions
- **🎯 Today's Priorities** - High-priority events, open PRs, and assigned issues
- **🚧 Blockers** - Automatically detect blocked or waiting items
- **💬 Team Updates** - GitHub mentions and important email notifications
- **🤖 Context-Aware** - Optional Context Engineering MCP integration for intelligent insights
- **⏰ Automated** - Runs daily at 7 AM via macOS launchd

---

## Preview

The briefing email includes:

- **Professional HTML formatting** with color-coded priorities
- **Activity statistics** (commits, PRs, lines changed)
- **Smart priority detection** based on keywords
- **Direct links** to all GitHub items and calendar events
- **Responsive design** that looks great on desktop and mobile

---

## Quick Start

### 1. Prerequisites

- macOS (Darwin)
- Python 3.13+ (already installed)
- Google Cloud account (for Gmail/Calendar APIs)
- GitHub Personal Access Token
- Git repositories you want to track

### 2. Installation

```bash
cd ~/Documents/morning-briefing
./setup.sh
```

The setup script will:
- Create Python virtual environment
- Install all dependencies
- Create configuration files from templates
- Install launchd scheduler
- Set up logging

### 3. Configuration

#### A. Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project named "Morning Briefing"
3. Enable APIs:
   - Gmail API
   - Google Calendar API
4. Create OAuth 2.0 credentials:
   - Application type: **Desktop app**
   - Name: "Morning Briefing Client"
5. Download `credentials.json`
6. Save to: `~/Documents/morning-briefing/credentials/credentials.json`

#### B. GitHub Access Token

1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Generate new token (classic)
3. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `read:user` (Read user profile data)
   - ✅ `read:org` (Read org and team membership)
4. Copy the token

#### C. Edit Configuration Files

**Edit `config.yaml`:**

```yaml
user:
  name: "Armando Diaz Silverio"
  email: "your@email.com"
  timezone: "America/Santo_Domingo"

github:
  username: "your-github-username"
  organizations:
    - "Exxede-Investments"
    - "ReppingDR"
    - "Prolici"
    - "Exxede-dev"
```

**Edit `secrets.yaml`:**

```yaml
github:
  access_token: "ghp_YOUR_GITHUB_TOKEN_HERE"
```

### 4. First Run (OAuth Authorization)

```bash
./test.sh --dry-run
```

This will:
- Open your browser for Google OAuth authorization
- Request access to Gmail and Calendar
- Save the authorization token
- Run a dry-run test (no email sent)

### 5. Test the System

```bash
./test.sh
```

This sends a real test email to verify everything works.

### 6. Activate Automation

The briefing is now scheduled to run every day at 7:00 AM automatically!

To run immediately:
```bash
launchctl start com.exxede.morning-briefing
```

---

## Usage

### Commands

```bash
# Test without sending email
./test.sh --dry-run

# Send test email
./test.sh

# Run immediately (triggers scheduled job)
launchctl start com.exxede.morning-briefing

# Check if scheduled job is loaded
launchctl list | grep morning-briefing

# View logs
tail -f ~/.local/logs/morning-briefing.log

# View error logs
tail -f ~/.local/logs/morning-briefing-error.log

# Uninstall automation (keeps project files)
./uninstall.sh

# Reinstall automation
./setup.sh
```

### Manual Execution

```bash
cd ~/Documents/morning-briefing
source venv/bin/activate
python3 main.py --verbose
```

---

## Configuration Guide

### Priority Keywords

Edit `config.yaml` to customize priority detection:

```yaml
priority_keywords:
  high: ["urgent", "critical", "asap", "important", "deadline", "launch"]
  medium: ["review", "meeting", "call", "check", "follow-up"]
  low: ["optional", "fyi", "info", "update"]
```

Calendar events and GitHub items containing these keywords will be highlighted.

### Blocker Detection

Configure keywords that indicate blocked items:

```yaml
blocker_keywords:
  - "blocked"
  - "waiting for"
  - "needs review"
  - "pending"
  - "stuck"
```

Issues containing these keywords will appear in the "Blockers" section.

### Email Filters

Filter important emails by keywords:

```yaml
email_filters:
  enabled: true
  days_lookback: 1
  keywords: ["urgent", "important", "asap", "deadline"]
  max_results: 10
```

### Schedule

To change the briefing time, edit `com.exxede.morning-briefing.plist`:

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>7</integer>  <!-- Change this -->
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

Then reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.exxede.morning-briefing.plist
launchctl load ~/Library/LaunchAgents/com.exxede.morning-briefing.plist
```

---

## Context Engineering MCP Integration

The system includes optional integration with the Context Engineering MCP for enhanced intelligence:

### Features When Enabled

- **Attractor-Based Priorities** - Learns what's truly important to you over time
- **Pattern Recognition** - Identifies recurring themes and projects
- **Smart Blocker Detection** - Flags items that have been present but unchanged
- **Context Persistence** - Briefing context survives across days
- **Intelligent Summarization** - Resonance-based content filtering

### Enabling Context MCP

In `config.yaml`:

```yaml
context_mcp:
  enabled: true
  inject_history: true
  use_attractors: true
  protocol_shell: true
```

**Note:** Context MCP integration is optional. The briefing works perfectly without it.

---

## Project Structure

```
morning-briefing/
├── main.py                          # Main orchestration script
├── config.yaml                      # User configuration
├── secrets.yaml                     # API credentials (gitignored)
├── requirements.txt                 # Python dependencies
├── .gitignore                       # Git ignore rules
│
├── modules/                         # Python modules
│   ├── __init__.py
│   ├── config_loader.py            # Configuration management
│   ├── gmail_service.py            # Gmail API integration
│   ├── calendar_service.py         # Calendar API integration
│   ├── github_service.py           # GitHub API integration
│   ├── email_formatter.py          # Email HTML generation
│   └── context_mcp_integration.py  # Context MCP features
│
├── templates/                       # Email templates
│   └── briefing_template.html      # Jinja2 HTML template
│
├── credentials/                     # OAuth credentials (gitignored)
│   ├── credentials.json            # Google OAuth client
│   └── token.json                  # Google OAuth token
│
├── logs/                            # Application logs
│
├── tests/                           # Unit tests (future)
│
└── scripts/
    ├── setup.sh                    # Installation script
    ├── test.sh                     # Testing script
    └── uninstall.sh                # Uninstall script
```

---

## Troubleshooting

### OAuth Authorization Issues

**Problem:** Browser doesn't open for OAuth
**Solution:** Run manually: `python3 main.py --verbose`

**Problem:** "Access blocked" from Google
**Solution:** Add your email as a test user in Google Cloud Console

### Email Not Sending

**Problem:** No email received
**Solution:**
1. Check logs: `tail -f ~/.local/logs/morning-briefing.log`
2. Verify Gmail API is enabled
3. Test with: `./test.sh`

### GitHub API Issues

**Problem:** "Bad credentials"
**Solution:**
1. Verify token in `secrets.yaml`
2. Check token has required scopes
3. Generate new token if needed

### Scheduled Job Not Running

**Problem:** Briefing doesn't run at 7 AM
**Solution:**
```bash
# Check if job is loaded
launchctl list | grep morning-briefing

# Check system logs
log show --predicate 'process == "launchd"' --last 1h | grep morning-briefing

# Manually trigger
launchctl start com.exxede.morning-briefing
```

### Check Logs

```bash
# Application logs
tail -f ~/.local/logs/morning-briefing.log

# Error logs
tail -f ~/.local/logs/morning-briefing-error.log

# System logs for launchd
log show --predicate 'eventMessage contains "morning-briefing"' --last 1d
```

---

## Development

### Running Tests

```bash
cd ~/Documents/morning-briefing
source venv/bin/activate
pytest tests/
```

### Adding New Features

1. Create module in `modules/`
2. Import in `main.py`
3. Add configuration to `config.example.yaml`
4. Update `README.md`
5. Test with `./test.sh --dry-run`

### Contributing

This is a personal automation tool, but feel free to:
- Fork and customize for your needs
- Submit bug reports
- Suggest improvements

---

## Security Notes

- **Never commit `secrets.yaml`** - It contains API credentials
- **Never commit `credentials/`** - Contains OAuth tokens
- **Use macOS Keychain** for production (see `secrets.yaml`)
- **Rotate tokens periodically** - GitHub and Google tokens
- **Review API permissions** - Grant minimum required scopes

---

## FAQ

**Q: Can I use this on Linux or Windows?**
A: Currently designed for macOS. Linux: replace launchd with cron. Windows: use Task Scheduler.

**Q: Will this work with multiple Google accounts?**
A: Yes, but you need separate credentials for each account.

**Q: Can I customize the email template?**
A: Yes! Edit `templates/briefing_template.html`

**Q: Does this use AI?**
A: Optional Context MCP integration uses neural field dynamics for pattern recognition.

**Q: What if I don't have Context MCP?**
A: The briefing works perfectly without it. Context MCP is an optional enhancement.

**Q: Can I receive multiple briefings per day?**
A: Yes, add multiple `StartCalendarInterval` entries in the plist file.

**Q: How do I backup my configuration?**
A: Copy `config.yaml` and `secrets.yaml` to a secure location (encrypted).

---

## Roadmap

Potential future enhancements:

- [ ] Slack/Discord notification support
- [ ] Web dashboard for configuration
- [ ] Mobile app for iOS/Android
- [ ] Team briefing aggregation
- [ ] Integration with project management tools (Jira, Linear, Asana)
- [ ] Natural language summaries with LLM
- [ ] Voice briefing via Siri/Alexa
- [ ] Weekly/monthly summary emails
- [ ] Customizable themes and layouts

---

## Credits

**Created by:** Armando Diaz Silverio
**Companies:**
- Exxede Investments
- ReppingDR
- Prolici
- Exxede.dev

**Technologies:**
- Python 3.13
- Google APIs (Gmail, Calendar)
- GitHub API
- Jinja2 templating
- macOS launchd
- Context Engineering MCP (optional)

---

## License

MIT

---

## Support

For issues or questions:
- Check logs: `~/.local/logs/morning-briefing.log`
- Review configuration: `config.yaml` and `secrets.yaml`
- Test components: `./test.sh --dry-run`
- Consult API documentation: [Google](https://developers.google.com) | [GitHub](https://docs.github.com)

---

**Enjoy your automated morning briefings!** ☀️📬

*Generated daily at 7:00 AM in Punta Cana timezone (America/Santo_Domingo)*
