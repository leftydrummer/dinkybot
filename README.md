### DISCLAIMER ⚠️

<strong>This is in an independent fan project and is NOT officially affiliated with Dinky Pod in any way</strong>

# DinkyBot

![DinkyBot Logo](assets/logo.webp)

(*please someone make better art*)

Made with ❤️ by Neill for the Dinky Podcast community 

https://dinkypod.com

## About DinkyBot
DinkyBot is a custom Discord bot created for the Dinky Podcast community, written in [Python](https://www.python.org). Huge shout out to the crew over at [Discord.py](https://github.com/Rapptz/discord.py) for making this easy and fun ❤️  <br><br> 
It's designed to add fun and utility (lol yeah right) to the Discord server. Right now it only has very basic functions such as posting GIFs related to community in-jokes, but my hope is that it can grow organically to serve the community. The sky is the limit!

Have an idea? Put in a [feature suggestion](https://github.com/leftydrummer/dinkybot/issues/new?template=feature_suggestion.yml)!

## Adding to Discord
The bot can be invited to be added to a server with link below

[Add Me to Discord 😎](https://discord.com/oauth2/authorize?client_id=1344839681929379880)

### 🛠 Required Permissions

The link above will present the user with an authorization flow- inviting the bot to the server and requesting the following permissions be granted to it. These are necessary for the bot to do what it do and I've tried to break them down below for transparency. 

#### View Channels
- Allows the bot to read the list of channels in a server
- Needs visibility into server channels in order to be able to send messages

#### Send Messages
- Allows the bot to post messages in text channels
- Needed in order to be able to post any content into a channel (GIFs, messages, etc)

#### Attach Files
- allows the bot to attach and upload files in messages
- This is needed for things like posting GIFs as the bot works by attach them to a message and uploado. 

#### Use Application Commands
- Grants the bot permission to use slash commands.
- Required to be able to have the bot register and use slash commands.

#### Message Content 
- Allows the bot to read the actual content of messages in the server.
- Needed in order to be able to respond to the content of messages, for example to do something in response to a particular phrase being used.
- ⚠️ NOTE: this is a spicy one because it technically grants access to user created data. We do not store or use this info in any other way than immediately processing the message to see if it contains a trigger phrase.  
<hr>
 



### Stuff it can do ⬇️ <br>



## Slash Commands

User initiated commands that make the bot perform actions. All users can access by typing "/" followed by the command

- **/weird** - Posts the "this is really weird" GIF 🦶
- **/dy** - Posts the "DINK YOURSELF" GIF

## Events

Things the bot does automatically in response to something occurring

- **Ready alert** - Sends a "Hello World!" message to the channel `general` when the bot handshakes with Discord and comes online.
<details>
<summary>Secret fun stuff 🤭</summary>
    
- **"This is weird" listener** - Automatically posts the "this is weird" GIF when a message in a channel contains "this is weird" or "this is really weird".
</details>
<br>
<footer>
Join the Dinky Podcast community to interact with DinkyBot and connect with fellow DINKs and SINKs!
</footer>