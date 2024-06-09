# bridgewatcher

***WARNING! This project is in the early stage of development. Do not expect the final result to be the same as the state of the project you can see right now. Use this application at your risk, as it may be updated in unexpected ways.***

Bridgewatcher is intended to be a useful and functional discord bot that crushes the latest data that can be found using the [Albion Online Data Project API](https://www.albion-online-data.com/). With this data the bot should be able to examine the data and make calculations and predictions for different groups of players all around Albion.

The project doesn't have a central host, so anyone who wants to you the bot, should check if the creator's instance is currently running (`Bridgewatcher#7151`) or should host the bot themselves.


## How do I use this?
Currently, the bot has three commands designed to facilitate or speed up the process of playing Albion Online.

First, let's look at the current configuration for your server using the `;info` command.

Here, under the server section, you can find the server from which the bot recieves information. Initially, upon joining, the bot uses American server.

To change the server, use the command `;set_server` followed by `america`, `europe` or `asia` to select the deisred server.

### Gold prices
Use `/gold` to get the gold prices and their difference over 3 hours. If you want to see more than 3 prices, specify a number from 1 to 24 after the command.

### Item prices
Depending on the selected server, `/price` will return the price of the item you must specify after the command name. You can find the item's name using [this link](https://github.com/ao-data/ao-bin-dumps/blob/master/formatted/items.txt). Here, all game items are listed in the format `NAME_UNDERSTOOD_BY_BOT: Name you understand`. Use `Ctrl + F` in your browser to search for items by their in-game names.

After calling this command, you'll receive a menu visible only to you. Here, you can specify more detailed information about the item you're looking for.

Use the **quality** menu to select the item's quality among normal, good, outstanding, excellent, and masterpiece. You can choose only one quality.

Use the **cities** menu to select the cities where you want to know the price. This include the black market.

### Craft items and refine materials
Use `/craft` to specify an item you want to create for the world of Albion Online.

After calling this command, you'll get a similar menu to the `/price` command where you can choose the city where you are crafting the item and the city where you sell it. Initially, the ctafting city is set to the city with a crafting bonus, and the sell city is set to the city with the highest price for the item.

Use the **resources** button to specify the amount of resources you have for creating the item. Each resource is labeled with a name understood by bot.

Use the **return rate** button to specify the return percentage. The percent symbol is not needed.


## How do I get this to work?
If you have chosen the path of self-hosting the bot, follow the instructions in this section. Keep in mind that the project is developed for UNIX-like operating systems, and attempts to make the project work on Microsoft Windows operating systems may not be successful (also, the commands are different).

### Create a new Discord application
Follow [this link](https://discord.com/developers/applications) to the Discord Developers portal and log in using your credentials. Visit the "Applications" tab and click "Create", give your bot a name and proceed.

Grant the bot all Gateway previleged intents in the "Bot" section, since Discord has become more stringent and specific with the permission you grant to the bot.

To invite the bot to a server, go to the "0auth2" section and select "bot" from the list you can see. Give the bot administrator permissions and copy the invite link down below.

### Launch the application
On the Discord Developers page within your application, go to the "Bot" tab and click on "Reset token". A new authorization token will appear for a short period of time, which you need to copy. We will use this to establish a connection with Discord using the `Discord py` library.

After cloning the repository, create a `.env` file in the root directory and inside the file, paste: `DISCORD_TOKEN="your token"`. Your token is the token you copied from the Discord Developers. The quotes are obbligatory.

Create a new Python environment using `python3 -m venv venv`, activate it with `source venv/bin/activate` and synchronize the dependencies using `pip3 install -r requirements.txt`.

To run the bot, execute `./bot.py run`.
