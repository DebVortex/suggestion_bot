# suggestion_bot

Discord bot that monitors suggestion channels and sort the messages by (reaction-)votes 

## Installation

Setup an virtualenvironment:

```
$ python3 -m venv venv
```

Activate it:

```
$ source venv/bin/activate
```

And finally, install the requirements:

```
$ pip install -r requirements.txt
```

## Configuration

The suggestion_bot uses environment variables for its configuration. It also
uses the python-dotenv package.

To configure this bot, you can create an `.env` file in the directory of the
`main.py` to set its environment variables.

The following environment variables are nessessary:

```
DISCORD_BOT_TOKEN
```

The following environment variables are optional:

* `LOG_LEVEL`. Can be one of the following: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, `EXCEPTION`. Defaults to `DEBUG`.
* `LOG_FILE`. File to write log messages to. Musst be a file path. If not set, it will log to stdout.
