# Scheduling Instructions

The monitoring script can be executed automatically.

## Windows Task Scheduler

1. Open Task Scheduler.
2. Create a Basic Task.
3. Choose Daily.
4. Select Start a Program.
5. Program:
   python
6. Arguments:
   monitoring.py

## Linux Cron

Example:

0 9 * * * python3 monitoring.py

This runs the monitoring script every day at 9:00 AM.
