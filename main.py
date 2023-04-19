import discord
from discord import app_commands
import json
import config

import requests
from bs4 import BeautifulSoup
import functools
import asyncio
import re


# ---------- GLOBAL VARIABLES ---------------


decks = [] # global variable to store deck objects
games = [] # global variable to store game objects


# ---------- CLASS DEFINITIONS ---------------


class MyClient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        # We need an `discord.app_commands.CommandTree` instance
        # to register application commands (slash commands in this case)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

        # load decks from local decks.json file
        pull_decks_from_database(config.deck_path)

    async def setup_hook(self) -> None:
        # Sync the application command with Discord.
        SERVER_ID = discord.Object(id=config.guild_id)
        self.tree.copy_global_to(guild=SERVER_ID)
        await self.tree.sync(guild=SERVER_ID)


class Deck:
    def __init__(self, owner, commander):
        self.owner = owner
        self.commander = commander
        self.rating = 1500
        self.wins = None
        self.losses = None

    def __str__(self):
        return f'{self.commander} ({self.owner})'


class Game:
    def __init__(self, date, winner, decks):
        self.date = date
        self.winner = winner
        self.decks = decks

    def __str__(self):
        # return f"{str(self.date)[:10]} {' vs '.join(self.decks)} **Win {self.winner}**"
        return f"**{self.winner} (Win)**  vs  {'  vs  '.join([x for x in self.decks if x != self.winner])}"


class PlayerSelect(discord.ui.Select):
    def __init__(self, parent_view):
        options = [discord.SelectOption(label=player) for player in set([x.owner for x in decks])]
        super().__init__(placeholder='Who played? Select 4 players', options=options, min_values=4, max_values=4)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await self.parent_view.add_dropdowns(interaction)


class DeckSelect(discord.ui.Select):
    def __init__(self, player, parent_view):
        player_decks = [x.commander for x in decks if x.owner == player]
        options = [discord.SelectOption(label=deck) for deck in player_decks]
        super().__init__(placeholder=f"Select a {player} deck", options=options, min_values=1, max_values=1)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # check to see if we have a selection for each player
        if all([x.values for x in self.parent_view.deck_select]):
            await self.parent_view.pick_winner(interaction)
        else:
            await interaction.response.defer()
        

class WinnerSelect(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=x) for x in self.parent_view.selected_decks]
        super().__init__(placeholder='Select the winner', options=options)
        
    async def callback(self, interaction: discord.Interaction):
        await self.parent_view.log_game(interaction)


class RegisterGameView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.player_select = PlayerSelect(self)
        self.add_item(self.player_select)

    async def add_dropdowns(self, interaction: discord.Interaction):
        '''Adds additional dropdowns to the view based on players selected'''

        # Remove player selection dropdown
        self.remove_item(self.player_select)

        # Add a new dropdown menu for each player (owner) that was selected
        self.deck_select = [DeckSelect(player, self) for player in self.player_select.values]
        for ea in self.deck_select:
            self.add_item(ea)

        # update view
        await interaction.response.edit_message(view=self)

    async def pick_winner(self, interaction: discord.Interaction):
        '''Add dropdown to select the winner'''

        # Set attribute to use in log_game method and WinnerSelect class
        self.selected_decks = [x.values[0] for x in self.deck_select]
        
        # Remove dropdowns and update view
        for ea in self.deck_select:
            self.remove_item(ea)

        # Add winner dropdown
        self.winner_select = WinnerSelect(self)
        self.add_item(self.winner_select)

        await interaction.response.edit_message(view=self)

    async def log_game(self, interaction: discord.Interaction):
        '''Called once all decks and winner have been selected to log the game'''
        
        # remove winner select dropdown
        self.remove_item(self.winner_select)

        game = Game(
            date = interaction.message.created_at,
            winner = self.winner_select.values[0],
            decks = self.selected_decks
            )
        games.append(game)

        await interaction.response.edit_message(content=game,view=self)
        

# ---------- FUNCTION DEFINITIONS ---------------


def read_file(path):
    '''Read json data from a file'''
    with open(path, 'r') as f:
        data = json.load(f)
    return data


def pull_decks_from_database(path):
    database = read_file(path)
    for owner, commanders in database.items():
        for commander in commanders:
            decks.append(Deck(owner,commander))
    print(f'Loaded {len(decks)} decks from {path}.')


# def to_thread(func):
#     @functools.wraps(func)
#     async def wrapper(*args, **kwargs):
#         return await asyncio.to_thread(func, *args, **kwargs)
#     return wrapper


# @to_thread
# def registerDecks(deck_links: dict):

#     def getCommanderName(link: str):

#         headers = {'User-Agent': 'python-requests/2.28.2',
#                    'Accept': 'text/html'}
#         response = requests.get(link, headers=headers)

#         if response.status_code//100 != 2:
#             return response
        
#         soup = BeautifulSoup(response.text, 'html.parser')

#         if link.startswith('https://www.mtggoldfish.com'):
#             # For mtggoldfish links, the commander is in an input element
#             commander_element = soup.find('input', {'name': 'deck_input[commander]'})
#             partner_element = soup.find('input', {'name': 'deck_input[commander_alt]'})
#             if partner_element.get('value') is None:
#                 return commander_element.get('value')
#             else:
#                 return commander_element.get('value') + ' / ' + partner_element.get('value')
#         elif link.startswith('https://www.moxfield.com'):
#             # For moxfield links, the commander is in the title element
#             title = soup.find('title').text
#             # Return text between parentheses
#             return title[title.index('Commander (') + 11:title.index(')')]
#         else:
#             return 'I can only process www.mtggoldfish.com or www.moxfield.com links at this time.'

#     # Replace links with Commander Names in deck_links
#     count = 0
#     for links in deck_links.values():
#         count += len(links)
#         for i in range(len(links)):
#             links[i] = getCommanderName(links[i])

#     # Write new dictionary to the decks database
#     with open(config.deck_path, 'w') as f:
#         f.write(json.dumps(decks, indent=4))

#     return count


# ---------- DISCORD BOT SLASH COMMANDS ---------------


client = MyClient()


# @client.tree.command()
# async def update_decks(interaction: discord.Interaction):
#     '''Register decks based on decklist links in #decklists channel'''
#     channel = client.get_channel(907783732033896479)
#     deck_links = {}
#     async for message in channel.history(limit=None):
#         # Use the regular expression to find links in each message
#         deck_links[message.author.name] = re.findall(r"(?P<url>https?://[^\s]+)", message.content)

#     count = await registerDecks(deck_links)
#     await interaction.response.send_message(f'{count} decks registered from #decklists channel', ephemeral=True)


@client.tree.command()
async def game(interaction: discord.Interaction):
    """Create a dropdown menu to record a new 4 player game"""
    view = RegisterGameView()
    await interaction.response.send_message(view=view)


client.run(config.discord_token)