# Bridgewatcher
![GitHub Tag](https://img.shields.io/github/v/tag/detectivekaktus/bridgewatcher)
![GitHub License](https://img.shields.io/github/license/detectivekaktus/bridgewatcher)
![GitHub Issues](https://img.shields.io/github/issues/detectivekaktus/bridgewatcher)
![GitHub Pull Requests](https://img.shields.io/github/issues-pr/detectivekaktus/bridgewatcher)



Bridgewatcher is a Discord bot built for simplifying crafting, trading and market flipping in Albion Online without the need of external applications: just you and your guild's Discord server.

You can host the bot by specifying all the required environment variables in `.env` from `.env.example` and running `docker compose up --build -d` or try adding it [via this link](https://discord.com/oauth2/authorize?client_id=1241428288195526796).

Huge thanks to the [Albion Online Data Project](https://www.albion-online-data.com/) for developing the API that powers the bot with latest price updates all over 3 Albion Online Servers.

## What are the commands that I can use?
* `/conf`: get configuration information
* `/server`: set Albion Online server
* `/gold`: get last 12 gold prices
* `/premium`: get any premium status price
* `/price`: get any item price
* `/craft`: get profit from crafting an item
* `/flip`: get profit from market flipping
* `/utc`: get UTC time

## What is this built with?
* Python
* MongoDB
* Redis
* Docker