# Devil X Mention Bot

A Telegram group mention bot that lets admins tag all members or admins at once.

## Features

- `/all` or `@all` or `/tagall` — Tag all group members
- `/admin` or `/tagadmin` — Tag all administrators
- `/cancel` — Stop an active tagging process
- `/addsudo` / `/desudo` / `/sudolist` — Manage sudo users per group
- `/broadcast` — Owner only: send a message to all users
- `/users` — Owner only: list all bot users

## Required Environment Variables

```
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_BOT_TOKEN=
BOT_OWNER_ID=
```

Get your API credentials from https://my.telegram.org  
Get your Bot Token from @BotFather on Telegram  
Get your user ID from @userinfobot on Telegram

---

## Deploy on Heroku

1. Create a new Heroku app
2. Set the environment variables under **Settings → Config Vars**
3. Connect your GitHub repo or push using Heroku CLI:

```bash
heroku login
heroku git:remote -a your-app-name
git push heroku main
```

4. Make sure the `worker` dyno is ON and the `web` dyno is OFF:

```bash
heroku ps:scale worker=1 web=0
```

---

## Deploy with Docker

```bash
docker build -t devil-x-mention-bot .
docker run -d \
  -e TELEGRAM_API_ID=your_api_id \
  -e TELEGRAM_API_HASH=your_api_hash \
  -e TELEGRAM_BOT_TOKEN=your_bot_token \
  -e BOT_OWNER_ID=your_user_id \
  devil-x-mention-bot
```

---

## Deploy on VPS / Local

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your values in .env
python bot.py
```

---

Made by [MR DEVIL](http://t.me/mrdevil12)
