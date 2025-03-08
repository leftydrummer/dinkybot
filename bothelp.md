# DinkyBot Help

DinkyBot is a Discord bot created for the Dinky Podcast community. It provides various features and commands to enhance the server experience.

## Feature Overview

- Post an alert for new podcast episodes
- Dedicated commands to grab the latest episode, as well as search back catalog
- Goofy stuff like posting GIFs and inside jokes based on triggers in messages
- Welcome new members

## Slash Commands
These are commands that any user can use by typing / followed by the command
Typing / will show a list of available commands in the app

### `/latest-episode`

**Parameters:**

- `private` (optional): If true, only you can see the response (default: true)

### `/search-episodes`

Search the podcast catalog by title

**Parameters:**

- `query`: The search query for the episode title
- `private` (optional): If true, only you can see the response (default: true)

### `/help`

Show bot help info

**Parameters:**

- `private` (optional): If true, only you can see the response (default: true)

## GIF Commands

These post a specific GIF

### `/weird`

Posts the 'this is weird' GIF

### `/dy`

Posts the DINK YOURSELF GIF

## Events
Occur in response to some type of trigger event 

### When *any* message gets posted:

- Responds to messages containing "this is really weird" or "this is weird" with a GIF
- Replies with a joke if a message contains negative sentiment about Lord of the Rings

### When a new member joins the server:

- Sends a welcome message and GIF to the `intros` channel

## Tasks
Bot will execute these on a defined schedule

### Podcast Feed Check

- Checks the podcast RSS feed every 10 minutes
- Sends an embed to the podcast-chatter channel if there's a new episode

*Made with ❤️ by <@257048354872229888>*
