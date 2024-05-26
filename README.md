# bridgewatcher

***WARNING! This project is in the early stage of development. Do not expect the final result to be the same as the state of the project you can see right now. Use this application at your risk, as it may be updated in unexpected ways.***

Bridgewatcher is intended to be a useful and functional discord bot that crushes the latest data that can be found using the [Albion Online Data Project API](https://www.albion-online-data.com/). With this data the bot should be able to examine the data and make calculations and predictions for:
1. Crafters. Crafters will be able to find out if making a certain equipment is profitable and where it is profitable.
2. Refiners. Refiners will be able to specify the amount of focus used when refining and so get the profit of doing this activity.
3. Traders. Traders should be able to ask the bot to send direct messages to users whenever the price of an item has reached one state or another.
4. And more!

The project doesn't have a central host, so anyone who wants to you the bot, should check if the creator's instance is currently running (`Bridgewatcher#7151`) or should host the bot themselves.

## How do I get this to work?
If you have chosen the path of self-hosting the bot, follow the instructions in this section. Keep in mind that the project is developed for UNIX-like operating systems, and attempts to make the project work on Microsoft Windows operating systems may not be successful (also, the commands are different).

### Create a new Discord application
Follow [this link](https://discord.com/developers/applications) to the Discord Developers portal and log in using your credentials. Visit the "Applications" tab and click "Create", give your bot a name and proceed.

Grant the bot all Gateway previleged intents in the "Bot" section, since Discord has become more stringent and specific with the permission you grant to the bot.

To invite the bot to a server, go to the "0auth2" section and select "bot" from the list you can see. Give the bot administrator permissions and copy the invite link down below.

### Launch the application
On the Discord Developers page within your application, go to the "Bot" tab and click on "Reset token". A new authorization token will appear for a short period of time, which you need to copy. We will use this to establish a connection with Discord using the `Discord py` library.

After cloning the repository, create a `.env` file in the root directory and inside the file, paste: `DISCORD_TOKEN=your token`. Your token is the token you copied from the Discord Developers.

Create a new Python environment using `python3 -m venv venv`, activate it with `source venv/bin/activate` and synchronize the dependencies using `pip3 install -r requirements.txt`.

Run the bot from `run.sh` script.
