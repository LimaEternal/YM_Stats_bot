@echo off
title Telegram Bot
call venv\Scripts\activate.bat
python bot_start.py
call venv\Scripts\deactivate.bat
exit