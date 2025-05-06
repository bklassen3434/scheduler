# 🥎 NCAA Softball RPI Scraper (2025)

This project collects and analyzes all 2025 NCAA Division I softball games and calculates RPI (Ratings Percentage Index) for each team based on actual results.

## 📊 What This Does

- Retrieves every D1 softball game result from February 8 to May 5, 2025
- Determines wins and losses for each team
- Calculates:
  - WP (Winning Percentage)
  - OWP (Opponents' Winning %)
  - OOWP (Opponents' Opponents' %)
  - Final RPI = 0.25 × WP + 0.50 × OWP + 0.25 × OOWP
- Saves the output to CSV for use in analytics or simulations

## 🚀 Why Use Docker?

The NCAA does not provide an official public API. Instead, we use [henrygd/ncaa-api](https://github.com/henrygd/ncaa-api), an open-source wrapper around the NCAA.com scoreboard.

This API:
- Mimics NCAA’s site structure
- Lets us download game data
- **Is easier and safer to run locally using Docker**

By using Docker:
- You avoid being rate-limited or blocked
- You don’t rely on a 3rd-party hosted version
- You can pull full-season data reliably in one go

## 📦 Folder Structure

