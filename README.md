
Eth2 Daily Tracker
===================
This is a Python (3.7+) tool to help you keep track of how much Ether you earn via staking (along with 
the price of ETH and so the fiat value of your staking rewards) on a day-to-day basis. 

Installation
============
Extract the files into their own folder and run eth2_daily_tracker.py from a CLI environment (Command Prompt or 
PowerShell in Windows or any Linux terminal) to see the modes of operation.

Modes of operation
==================

`eth2_daily_tracker.py loop` or `eth2_daily_tracker.py l` - Update the saved data every x (default: 5) minutes. 
Use this mode if you want to run the script in a terminal demultiplexer like tmux or screen.

`eth2_daily_tracker.py update` or `eth2_daily_tracker.py u` - Update the saved data once and then exit. Use this
mode if you want to run the script via crontab or a task scheduler.

`eth2_daily_tracker.py show` or `eth2_daily_tracker.py s` - Generate a report to display the saved data. The 
default period is the last week but you can alter this with `--date-from`/`--date-to` (to go for a historical range) args or `--since` (the number of days ago you want to start the range from)

The config.ini file
===================
This is generated when you first run the script. You need a CoinMarketCap API key. To obtain one, go to 
https://pro.coinmarketcap.com/ and then paste it in when asked. 

You also need to either know the indexes of your validator(s) or the eth1 address of the wallet you used
to send the deposits to create your validators.

The default currency is USD (all ETH prices are saved in it) but you can specify a different currency to
display the ETH price and daily earnings in the config file or (more temporarily) by running the `show` mode with `-c/--currency` followed by the symbol (eg EUR) of your choice.
