import discord
from discord import app_commands
import config
import deckstats
import re
from datetime import datetime


# ---------- CLASS DEFINITIONS ---------------


class Player:
    def __init__(self, name):
        self.name = name
        self.rating = 1500
        self.gold = 0
        self.wins = 0
        self.losses = 0


class Deck:
    def __init__(self, owner, commander, decklist, rating, wins, losses):
        self.owner = owner
        self.commander = commander
        self.decklist = decklist
        self.rating = rating
        self.wins = wins
        self.losses = losses

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

        # load decks from local json file
        self.decks = [Deck(**deck) for deck in deckstats.read_file(config.deck_path)]
        print(f'Loaded {len(self.decks)} decks from {config.deck_path}')

        # load games from local json file
        self.games = [Game(**game) for game in deckstats.read_file(config.game_path)]
        print(f'Loaded {len(self.games)} games from {config.game_path}')

    async def setup_hook(self) -> None:
        # Sync the application command with Discord.
        SERVER_ID = discord.Object(id=config.guild_id)
        self.tree.copy_global_to(guild=SERVER_ID)
        await self.tree.sync(guild=SERVER_ID)

        
class PlayerSelect(discord.ui.Select):
    def __init__(self, parent_view):
        options = [discord.SelectOption(label=player) for player in set([x.owner for x in client.decks])]
        super().__init__(placeholder='Who played? Select 4 players', options=options, min_values=4, max_values=4)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await self.parent_view.add_dropdowns(interaction)


class DeckSelect(discord.ui.Select):
    def __init__(self, player, parent_view):
        player_decks = [x.commander for x in client.decks if x.owner == player]
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

        # take player and commander names and find the correct deck object
        # self.player_select.values = ['gzy', 'DrSull', 'ostertoaster10', 'Spenda4life'] 
        # self.selected_decks = ['Breena, the Demagogue', 'Najeela, the Blade-Blossom', 'Prossh, Skyraider of Kher', 'Ghired, Conclave Exile']
        # dict(zip(self.player_select.values, self.selected_decks))

        # add game to games
        client.games.append(Game(
            date = interaction.message.created_at.strftime('%m-%d-%Y'),
            winner = self.winner_select.values[0],
            decks = self.selected_decks))
        
        # write to game database
        deckstats.write_file([game.__dict__ for game in games], config.game_path)

        await interaction.response.edit_message(content=client.games[-1],view=self)
        print(f'New game added: {client.games[-1]}')
        

# ---------- FUNCTION DEFINITIONS ---------------


async def load_decks_from_discord():
    """Use links in #decklists channel to load decks"""

    new_links = 0
    channel = client.get_channel(config.decklist_channel)
    async for message in channel.history(limit=None):
        # Use the regular expression to find links in each message
        for link in re.findall(r"(?P<url>https?://[^\s]+)", message.content):
            if link not in [deck.decklist for deck in client.decks]:
                # if a new link is found, get commander and add new deck
                new_links += 1
                commander = deckstats.get_commander_name(link)
                new_deck = Deck(owner=message.author.name, commander=commander, 
                                decklist=link, rating=1500, wins=0, losses=0)
                client.decks.append(new_deck)

    if new_links > 0:
        # save decks to json file
        deckstats.write_file([deck.__dict__ for deck in client.decks], config.deck_path)
        return f'{new_links} new deck(s) added to deck database'
    else:
        return 'No new decklists found'


# ---------- DISCORD BOT SLASH COMMANDS ---------------


client = MyClient()


@client.tree.command()
async def pull_decks(interaction: discord.Interaction):
    """Get decklist links in #decklists channel"""

    await interaction.response.send_message(
        'Loading decks from #decklists channel', 
        ephemeral=True)
    response = await load_decks_from_discord()
    await interaction.followup.send(response, ephemeral=True)


@client.tree.command()
async def game(interaction: discord.Interaction):
    """Create a dropdown menu to record a new 4 player game"""
    view = RegisterGameView()
    await interaction.response.send_message(view=view)


if __name__=='__main__':
    client.run(config.discord_token)