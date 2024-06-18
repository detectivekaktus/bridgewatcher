# bridgewatcher

Bridgewatcher is intended to be a useful and functional discord bot that crushes the latest data that can be found using the [Albion Online Data Project API](https://www.albion-online-data.com/) and the [SandboxInteractive API](https://www.tools4albion.com/api_info.php). With this data the bot should be able to examine the data and make calculations and predictions for different groups of players all around Albion.

Add the bot by following [this link](https://discord.com/oauth2/authorize?client_id=1241428288195526796&permissions=8&scope=bot) or if you want to host your own instance of the bot, go ahead to the **How do I get this to work?** section!

Any contributions that make the bot more simplier to use and more useful are welcome!

## What are the commands that I can use?
- `/info`: get the configuration information.
- `;set_server`: set the Albion Online server.
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

## How do I find in-game items?
Usage of most bot's commands depends on the item names that are different from the in-game once. You can find the full list of items [here](https://github.com/ao-data/ao-bin-dumps/blob/master/formatted/items.txt). Use `Ctrl + F` to write the name of the item you want to find and copy the value to the left from the result.

## How do I get this to work?
If you have chosen the path of self-hosting the bot, follow the instructions in this section.

### Create a new Discord application
Follow [this link](https://discord.com/developers/applications) to the Discord Developers portal and log in using your credentials. Visit the "Applications" tab and click "Create", give your bot a name and proceed.

Grant the bot all Gateway previleged intents in the "Bot" section, since Discord has become more stringent and specific with the permission you grant to the bot.

To invite the bot to a server, go to the "0auth2" section and select "bot" from the list you can see. Give the bot administrator permissions and copy the invite link down below.

### Launch the application
On the Discord Developers page within your application, go to the "Bot" tab and click on "Reset token". A new authorization token will appear for a short period of time, which you need to copy. We will use this to establish a connection with Discord using the `Discord py` library.

After cloning the repository, create a `.env` file in the root directory and inside the file, paste: `DISCORD_TOKEN="your token"`. Your token is the token you copied from the Discord Developers. The quotes are obbligatory. If you also want to add a separate application as a debug version of the current application, specify `DEBUG_TOKEN="token"` following the steps you've done before.

Create a new Python environment using `python3 -m venv venv`, activate it with `source venv/bin/activate` and synchronize the dependencies using `pip3 install -r requirements.txt`.

To run the bot, execute `./bot.py run`.
