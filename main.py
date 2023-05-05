import discord
from discord import app_commands
import config
import deckstats
import re
# from datetime import datetime


# ---------- CLASS DEFINITIONS ---------------


class MyClient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.default())
        # We need an `discord.app_commands.CommandTree` instance
        # to register application commands (slash commands in this case)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

        # load objects from json files
        self.decks = deckstats.load_json_data('decks.json',deckstats.Deck)
        self.games = deckstats.load_json_data('games.json',deckstats.Game)

    async def setup_hook(self) -> None:
        # Sync the application command with Discord.
        SERVER_ID = discord.Object(id=config.guild_id)
        self.tree.copy_global_to(guild=SERVER_ID)
        await self.tree.sync(guild=SERVER_ID)

        TEST_SERVER = discord.Object(id=config.test_guild)
        self.tree.copy_global_to(guild=TEST_SERVER)
        await self.tree.sync(guild=TEST_SERVER)

        
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

        # add game to games
        client.games.append(deckstats.Game(
            date = interaction.message.created_at.strftime('%m-%d-%Y'),
            winner = self.winner_select.values[0],
            decks = self.selected_decks))
        
        # write to game database
        deckstats.save_to_json(client.games,'games.json')
        
        await interaction.response.edit_message(content=client.games[-1],view=self)
        print(f'New game added: {client.games[-1]}')


# ---------- DISCORD BOT SLASH COMMANDS ---------------


client = MyClient()


@client.tree.command()
async def pull_decks(interaction: discord.Interaction):
    """Add decks from decklist links in #decklists channel"""

    await interaction.response.send_message(
        'Loading decks from #decklists channel', 
        ephemeral=True)

    new_links = 0
    channel = client.get_channel(config.decklist_channel)
    async for message in channel.history(limit=None):
        # Use the regular expression to find links in each message
        for link in re.findall(r"(?P<url>https?://[^\s]+)", message.content):
            if link not in [deck.decklist for deck in client.decks]:
                # if a new link is found, get commander and add new deck
                new_links += 1
                commander = deckstats.get_commander_name(link)
                new_deck = deckstats.Deck(owner=message.author.name, commander=commander, 
                                decklist=link, rating=1500, wins=0, losses=0)
                client.decks.append(new_deck)

    if new_links > 0:
        # save decks to json file
        deckstats.save_to_json(client.decks, 'decks.json')
        response = f'{new_links} new deck(s) added to deck database'
    else:
        response = 'No new decklists found'
    
    await interaction.edit_original_response(content=response)


@client.tree.command()
async def game(interaction: discord.Interaction):
    """Create a dropdown menu to record a new 4 player game"""
    view = RegisterGameView()
    await interaction.response.send_message(view=view)


@client.tree.command()
@app_commands.describe(dice='Enter dice in NdN format')
async def roll(interaction: discord.Interaction, dice: str):
    """Rolls a dice in NdN format."""
    await interaction.response.send_message(
        f'{dice}:  {deckstats.roll(dice)}')


@client.tree.command()
@app_commands.describe(query='Enter a scryfall search query')
async def scryfall(interaction: discord.Interaction, query: str):
    """Search scryfall"""
    result_limit = 5
    await interaction.response.send_message(
        f'{deckstats.scryfall_search(query, result_limit)}')


if __name__=='__main__':
    client.run(config.discord_token)