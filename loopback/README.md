# Loopback

It is a utility that helps implement chatting between personas, so that persona A talks to persona B and persona B talks to persona A. This may be useful for testing or simulating long-term communication with a real user. The utility works by implementing the Telegram Bot API interface.

## Run

1. Configure and start the loopback:

    ```bash
    python3 -m loopback.main
    ```

2. Configure and start the app:

    ```bash
    docker compose up --build
    ```

3. Bootstrap a conversation:

    ```bash
    python3 -m loopback.cli send-message http://127.0.0.1:8000/webhook 1 /start
    ```

Using the CLI, you can send messages to the app on behalf of a specific chat and control its state.

## Configuration

### Loopback

In the current (`loopback`) directory, create the `config.yml` file and fill it with the following settings:

<details>
<summary>Overview</summary>

| Name | Description | Default |
| --- | --- | --- |
| `host` | Host address used by the loopback HTTP server. | `0.0.0.0` |
| `port` | Port used by the loopback HTTP server. | `9000` |
| `access_log` | Enables access logging. | `false` |
| `webhook_url` | Telegram webhook URL that loopback forwards updates to. | `http://127.0.0.1:8000/webhook` |
| `webhook_secret_token` | Secret token sent with forwarded webhook requests. | `` |
| `sleep` | Delay in seconds before forwarding a message to the webhook. `0` means no delay. | `0` |
| `skip_commands` | Skips forwarding messages that are related to a command. | `true` |
| `max_messages` | Maximum number of messages to forward. `0` means no limit. | `0` |
| `chat_id_to_chat_id` | Mapping from incoming chat IDs to forwarded chat IDs. | `{}` |
| `chat_id_to_user_id` | Mapping from incoming chat IDs to forwarded user IDs. | `{}` |
| `chat_id_to_username` | Mapping from incoming chat IDs to forwarded usernames. | `{}` |
| `chat_id_to_first_name` | Mapping from incoming chat IDs to forwarded first names. | `{}` |
| `chat_id_to_last_name` | Mapping from incoming chat IDs to forwarded last names. | `{}` |

</details>

### App

Configure the app in the way you want to run it. The only settings you need to change to connect the app to the loopback are:

<details>
<summary>Config</summary>

```yaml
# Point to the loopback HTTP server.
# <ip> can be any of your computer local addresses that are reachable from
# the Docker container, for example LAN IP or Wi-Fi card IP.
telegram_origin: "http://<ip>:9000"

# The loopback will forward messages to the app webhook endpoint.
telegram_webhook_enable: true

# Disable request timeouts as they are not compatible with `sleep`.
telegram_timeout: 0

# Disable response splitting as it is not compatible with `sleep`.
output_separator: ""
```

</details>

## Examples

An example configuration that links chats 1 and 2 in the same app instance and caps a conversation at 10 messages:

<details>
<summary>Config</summary>

```yaml
sleep: 15
max_messages: 10
chat_id_to_chat_id:
    1: 2
    2: 1
chat_id_to_user_id:
    1: 100
    2: 200
```

</details>
