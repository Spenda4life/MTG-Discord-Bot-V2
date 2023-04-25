import discord
from discord import app_commands
import config
import deckstats
import re


# ---------- GLOBAL VARIABLES ---------------


players = []
decks = []
games = []


# ---------- CLASS DEFINITIONS ---------------


class Player:
    def __init__(self, name):
        self.name = name
        self.rating = 1500
        self.gold = 0
        self.wins = None
        self.losses = None


class Deck:
    def __init__(self, owner, commander, decklist):
        self.owner = owner
        self.commander = commander
        self.decklsit = decklist
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
        return f"**{self.winner} (Win)**  vs  {'  vs  '.join([x for x in self.decks if x != self.winner])}"


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


def pull_decks_from_database(path):
    database = deckstats.read_file(path)
    for owner, commanders in database.items():
        for commander in commanders:
            decks.append(Deck(owner,commander))
    print(f'Loaded {len(decks)} decks from {path}.')


# ---------- DISCORD BOT SLASH COMMANDS ---------------


client = MyClient()


@client.tree.command()
async def pull_decks(interaction: discord.Interaction):
    '''Register decks based on decklist links in #decklists channel'''
    channel = client.get_channel(config.decklist_channel)
    async for message in channel.history(limit=None):
        owner = message.author.name
        # Use the regular expression to find links in each message
        links = re.findall(r"(?P<url>https?://[^\s]+)", message.content)
        for link in links:
            decks.append(Deck(owner, deckstats.getCommanderName(link), link))


@client.tree.command()
async def game(interaction: discord.Interaction):
    """Create a dropdown menu to record a new 4 player game"""
    view = RegisterGameView()
    await interaction.response.send_message(view=view, ephemeral=True)


client.run(config.discord_token)