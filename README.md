# 📝 Discord Logger Bot

A Discord bot that logs **deleted, edited, and bulk-deleted messages** to dedicated channels.
Built with [discord.py](https://discordpy.readthedocs.io/), it uses slash commands for easy setup and management.

---

## ✨ Features

* 🔒 **Configurable log channels** (`/setup`)
* 🗑️ Logs **deleted messages** (with optional file if too long)
* ✏️ Logs **edited messages** (before & after content)
* 🧹 Logs **bulk deletions** (with text file export)
* 🎭 **Role & text exemptions**
* ⏸️ **Pause/unpause logging**
* 🧪 `/testlog` for verifying setup
* ⚙️ Saves settings per server in `config.json`

---

## 📂 Project Structure

```bash
discord-logger-bot/
│── src/
│   └── bot.py          # Main bot code
│── config.json         # Auto-generated per-server config
│── .env.example        # Template for environment variables
│── requirements.txt    # Python dependencies
│── .gitignore          # Ignore unnecessary files
│── README.md           # Documentation
│── LICENSE             # License (MIT recommended)
```

---

## 🚀 Getting Started

### 1️⃣ Prerequisites

* [Python 3.8+](https://www.python.org/downloads/)
* A [Discord Bot Application](https://discord.com/developers/applications)

  * Create a new bot
  * Enable **Privileged Gateway Intents**:

    * ✅ Message Content Intent
    * ✅ Server Members Intent
  * Copy your **Bot Token** (we’ll use it later)

---

### 2️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/discord-logger-bot.git
cd discord-logger-bot
```

---

### 3️⃣ Setup Environment

It’s recommended to use a **virtual environment**:

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

---

### 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 5️⃣ Configure Environment Variables

Copy the example file:

```bash
cp .env.example .env
```

Edit `.env` and insert your bot token:

```env
DISCORD_BOT_TOKEN=your-bot-token-here
```

⚠️ Never share your real `.env` file or commit it to GitHub.

---

### 6️⃣ Run the Bot

```bash
python src/bot.py
```

If successful, the console will show:

```
Bot logged in as <your-bot-name>
Registered commands:
- setup: Configure the logger bot
- pause: Pause logging for a set duration
...
```

---

## 🛠 Usage & Commands

### 🔧 Setup

* `/setup <channel>` → Add a channel where logs will be sent

### ⏸️ Control

* `/pause <minutes>` → Pause logging
* `/unpause` → Resume immediately

### 🎭 Exemptions

* `/exempt <text>` → Add exempt text (ignored if deleted/edited)
* `/removeexempt <text>` → Remove exempt text
* `/exemptrole <role>` → Add exempt role

### ⚙️ Configuration

* `/reset` → Reset server config
* `/status` → Show current config
* `/testlog` → Send a test log
* `/help` → Show all commands

---

## 📜 Configuration File

The bot automatically creates **`config.json`** to store server-specific settings:

Example:

```json
{
  "123456789012345678": {
    "channels": [987654321098765432],
    "exempt_roles": [123123123123123123],
    "exempt_texts": ["hello world"],
    "paused_until": null
  }
}
```

You normally **don’t edit this manually** — use slash commands instead.

---

## ❓ Troubleshooting

### Bot not responding?

* Ensure you **invited the bot with proper permissions** (`Manage Messages`, `View Audit Log`, `Read Messages`, `Send Messages`, `Embed Links`).
* Enable **Message Content Intent** in the [Discord Developer Portal](https://discord.com/developers/applications).

### Logs not showing up?

* Double-check that you ran `/setup <channel>` in your server.
* Ensure the bot has **permission to send messages** in the log channel.

### Error: `DISCORD_BOT_TOKEN is not set`

* Verify your `.env` file exists and has the correct format:

  ```
  DISCORD_BOT_TOKEN=your-token-here
  ```
* Ensure you ran the bot with the correct working directory:

  ```bash
  python src/bot.py
  ```

---

## 🧑‍💻 Contributing

Contributions are welcome!

1. Fork the repo
2. Create a feature branch (`git checkout -b feature-name`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to your branch (`git push origin feature-name`)
5. Open a Pull Request

---

## ⚖️ License

This project is licensed under the **MIT License**.
You are free to use, modify, and distribute it with attribution.
