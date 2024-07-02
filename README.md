# bridgewatcher

Bridgewatcher is intended to be a useful and functional discord bot that crushes the latest data that can be found by using the [Albion Online Data Project API](https://www.albion-online-data.com/) and the [SandboxInteractive API](https://www.tools4albion.com/api_info.php). With this data the bot should be able to examine the data and make calculations and predictions for different groups of players all around Albion.

Add the bot by following [this link](https://discord.com/oauth2/authorize?client_id=1241428288195526796&permissions=8&scope=bot) or if you want to host your own instance of the bot, go ahead to the **[How do I get this to work?](https://github.com/detectivekaktus/bridgewatcher?tab=readme-ov-file#how-do-i-get-this-to-work)** section!

## What are the commands that I can use?
- `/help`: get general help over the bot.
- `/info`: get the bot configuration information.
- `/server`: set the Albion Online server to pull information from.
- `/gold`: get past gold prices up to 24 hours.
- `/premium`: get premium price with the current gold price.
- `/price`: get the price of an item on the markets of Brecilien, Caerleon, Martlock, Thetford, Fort Sterling, Lymhurst, Bridgewatch, and Black Market.
- `/craft`: get crafting profit from the craft of an item.
- `/flip`: get profit from transporting an item from a royal city market to the black market.
- `/utc`: get UTC time.
- `/player`: get general information about a player.
- `/deaths`: get general information about the player's deaths.
- `/kills`: get general information about the player's kills.
- `/guild`: get general information about a guild.
- `/members`: get members of the guild.

## I want to contribute!
Any help that improves the project aesthetically or internally are always welcomed no matter how complex your change is. Read the [CONTRIBUTING.md](https://github.com/detectivekaktus/bridgewatcher/blob/master/CONTRIBUTING.md) file and open a pull request!

For new contributors there's a scheme that explains how the project is currently organized:
```
res:             -> 3rd party information that the bot relies on when first starting.
src:
  - commands:    -> `Cog` classes.
  - components:  -> reusable UI components.
  - config:      -> configuration logic.
  - db:          -> database logic.
  - utils:       -> helper functions and classes.
  - api.py       -> utilities to interact with 3rd party APIs.
  - client.py    -> bot definition.
  - constants.py -> constant values.
  - market.py    -> market calculations.
```

## How do I get this to work?
If you have chosen the path of self-hosting the bot, follow the instructions in this section.

### Create a new Discord application
Follow [this link](https://discord.com/developers/applications) to the Discord Developers portal and log in using your credentials. Visit the "Applications" tab and click "Create", give your bot a name and proceed.

Grant the bot all Gateway previleged intents in the "Bot" section, since Discord has become more stringent and specific with the permission you grant to the bot.

To invite the bot to a server, go to the "0auth2" section and select "bot" from the list you can see. Give the bot administrator permissions and copy the invite link down below.

### Launch the application
On the Discord Developers page within your application, go to the "Bot" tab and click on "Reset token". A new authorization token will appear for a short period of time, which you need to copy. We will use this to establish a connection with Discord using the `Discord py` library.

After cloning the repository, create a `.env` file in the root directory and inside the file, paste: `DISCORD_TOKEN="your token"`. Your token is the token you copied from the Discord Developers. The quotes are obbligatory. If you also want to add a separate application as a debug version of the current application, specify `DEBUG_TOKEN="token"` following the steps you've done before.

The application is launched with Docker, so we need to create a container from the image that we have in the root directory of the project, you can do this by typing `docker build -t bridgewatcher .`. Now run the container with `docker run bridgewatcher`.

## Buy me a host!
You can support me and the project with only $3.00/month on [Patreon](https://www.patreon.com/detectivekaktus) to help me pay for the bot hosting!
