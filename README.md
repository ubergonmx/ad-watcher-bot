# Ad Watcher Bot

This bot automates watching video ads from a website, and sends a screenshot proof to a WhatsApp group.

## Features

- Automated login and task completion.
- Takes screenshots of completed tasks.
- Sends screenshots to a WhatsApp group.
- Cross-platform support (macOS, Windows, Linux).
- Automated setup script.
- macOS permission checker.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/ubergonmx/ad-watcher-bot.git
cd ad-watcher-bot
```

### 2. Run the setup script

This will install dependencies and create a `.env` file for you.

```bash
python setup.py
```

### 3. Configure your credentials

Edit the `.env` file with your credentials.

```
WEBSITE_USERNAME=your_username
WEBSITE_PASSWORD=your_password
FUND_PASSWORD=your_fund_password
```

### 4. For macOS users

Before running the bot, check for the required permissions:

```bash
python check_macos_permissions.py
```

This utility will guide you if any permissions are missing. **Accessibility** permission is critical for the bot to work.

#### Required Permissions

The following permissions must be granted in macOS System Preferences:

**Accessibility Access**
![Accessibility Access](images/accessibility-access.png)

**Screen Recording Access**
![Screen Recording Access](images/screen-recording-access.png)

**Automation Access**
![Automation Access](images/automation-access.png)

### 5. Run the bot

```bash
python main.py
```

## Disclaimer

This bot is for educational purposes only. The user is responsible for complying with the terms of service of any website they use this bot on. The developers are not responsible for any misuse of this bot.