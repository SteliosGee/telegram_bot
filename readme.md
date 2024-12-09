# Telegram Bot: Subscription Management

This Telegram bot manages subscriptions and provides functionalities like adding subscribers, removing subscribers, listing all subscribers, and sending subscription expiry notifications.

## Features

1. **Start Command**: Greets the user.
2. **Add Subscriber**: Allows users to subscribe to the service and records their chat ID, username, and subscription date.
3. **Remove Subscriber**: Enables users to unsubscribe from the service.
4. **List Subscribers**: Provides a list of all subscribers with their details.
5. **Subscription Notifications**: Sends reminders about subscription expirations two days before the expiry date.

---

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Create a new bot using [BotFather](https://telegram.me/BotFather).
2. Replace the `TOKEN` variable in the `main.py` file with the token provided by BotFather.
3. Run the bot using the following command:

```bash
python bot.py
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
