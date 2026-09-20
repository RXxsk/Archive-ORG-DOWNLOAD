@echo off
cd /d "%~dp0"
py -3 2doarchive.py %*
if errorlevel 1 python 2doarchive.py %*
