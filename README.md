# Pokemon-raid-bot
A discord Bot for Pokemon Go raid coordination.
Currently the Bot can only create Polls.

# Setup

#### 1. Install the discord python package usign pip3: 
```
pip3 install discord.py
```
#### 2. Adjust config.ini
```

[bot]
token = <bot_token>

[database]
host = localhost
database = db_name
user = user_name
password = password
port = 3306
dialect = mysql
driver = mysqlconnector
```
The db + user must exists

#### 3. Run the bot

```
python3 start_bot.py
```

## Docker deployment
- TODO
