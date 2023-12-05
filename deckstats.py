import json
import requests
from bs4 import BeautifulSoup
import random
import os
import random


class Player:
    def __init__(self, name, rating=1500, 
                 gold=300, wins=0, losses=0):
        self.name = name
        self.rating = rating
        self.gold = gold
        self.wins = wins
        self.losses = losses


class Deck:
    def __init__(self, owner, commander, decklist=None, 
                 rating=1500, wins=0, losses=0):
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
    

class Card:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def register_game(date, winner, decks):
    """Wrtie new game to json file"""
    games = load_json_data('games.json', Game)
    new_game = Game(date,winner,decks)
    games.append(new_game)
    save_to_json(games,'games.json')
    return new_game


def load_json_data(file_name, cls):
    """Load json data to class objects"""
    path = os.path.join(os.path.dirname(__file__), file_name)
    return [cls(**obj) for obj in read_file(path)]


def save_to_json(objects: list, file_name):
    """Save list of class objects to json file"""
    path = os.path.join(os.path.dirname(__file__), file_name)
    write_file([x.__dict__ for x in objects], path)


def read_file(path):
    '''Read json data from a file'''
    with open(path, 'r', encoding="utf-8") as f:
        data = json.load(f)
    return data


def write_file(data, path):
    '''Write json data to a file'''
    with open(path, 'w') as f:
        f.write(json.dumps(data, indent=4))
        # f.write(json.dumps(data))


def elo(k_factor: int, d_factor: int, ratings: list, winner_indx: int):
    '''Function takes two or more ratings and returns new ratings'''

    new_ratings = []
    for indx, rating in enumerate(ratings):
        new_ratings.append(
             round(rating + k_factor * ((indx == winner_indx) - multi_ev(d_factor, ratings, indx))))

    return new_ratings


def multi_ev(d_factor: int, ratings: list, indx: int):
        '''returns a psudo average expected value of the indx rating against the others'''

        sum_ev = 0 
        for i, rating in enumerate(ratings):
            sum_ev += 1 / (1 + 10 ** ((rating - ratings[indx]) / d_factor)) if i != indx else 0

        return sum_ev / (len(ratings) * (len(ratings) - 1) / 2)


def get_commander_name(link: str):
    """Takes a decklist link and return the name of the commander"""

    headers = {'User-Agent': 'python-requests/2.28.2',
                'Accept': 'text/html'}
    response = requests.get(link, headers=headers)

    if response.status_code//100 != 2:
        return response
    
    soup = BeautifulSoup(response.content, 'html.parser')

    if link.startswith('https://www.mtggoldfish.com'):
        # For mtggoldfish links, the commander is in an input element

        commander_element = soup.find(
            'input', {'name': 'deck_input[commander]'})
        partner_element = soup.find(
            'input', {'name': 'deck_input[commander_alt]'})
        
        commander_name = commander_element.get('value')
        partner_name = partner_element.get('value')

        if partner_name is None:
            return commander_name
        else:
            # return commander_element.get('value') + ' / ' + partner_element.get('value')
            return f"{commander_name} / {partner_name}"
        
    elif link.startswith('https://www.moxfield.com'):
        # For moxfield links, the commander is in the title element
        title = soup.find('title').text
        # Return text between parentheses
        return title[title.index('Commander (') + 11:title.index(')')]
    
    else:
        return 'I can only process www.mtggoldfish.com or www.moxfield.com links at this time.'


def random_decks(decks: list[object], players=None):
    """Returns a random deck for each player"""
    if players == None:
        players = random.sample(list(set([x.owner for x in decks])), k=4)

    return [random.choice([deck for deck in decks if deck.owner == player]) for player in players]


def roll(dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        return 'Format has to be in NdN!'

    return ', '.join(str(random.randint(1, limit)) for _ in range(rolls))


def scryfall_search(query, limit):
    # Format text for query url and send the GET request
    query.replace(' ', '+').replace(':', '%3A')
    response = requests.get(f'https://api.scryfall.com/cards/search?q={query}')
    response_json = response.json()
    output = ''
    for card in [card['id'] for card in response_json['data']][:limit]:
        text = requests.get(f'https://api.scryfall.com/cards/{card}?format=text&pretty=true')
        output += f'{text.text}\n\n'
    return output[:2000]


def scryfall_bulk_data():
    """Use scryfall API to pull bulk card data"""

    headers = {'User-Agent': 'python-requests/2.28.2'}
    link = 'https://api.scryfall.com/bulk-data'
    response = requests.get(link, headers=headers)

    if response.status_code//100 != 2:
        print(response.status_code)

    response_json = json.loads(response.text)
    oracle_cards = [x for x in response_json['data'] if x['type'] == 'oracle_cards'][0]
    download_uri = oracle_cards['download_uri']
    bulk_data_response = requests.get(download_uri, headers=headers)

    file_name = 'scryfall_data.json'
    path = f'{os.path.dirname(__file__)}\{file_name}'
    with open(path, 'wb') as file:
            file.write(bulk_data_response.content)


def load_game_database():
    """Load players, decks, and games from saved json files"""

    players = load_json_data('players.json', Player)
    decks = load_json_data('decks.json', Deck)
    games = load_json_data('games.json', Game)

    # replace text with deck objects for each game
    for game in games:
        game.winner = next((deck for deck in decks if f'{deck.commander} ({deck.owner})' == game.winner), None)
        game.decks = [next((deck for deck in decks if f'{deck.commander} ({deck.owner})' == deck_name), None) 
                      for deck_name in game.decks] 

    # replace owner with player object for each deck
    for deck in decks:
        deck.owner = next((player for player in players if player.name == deck.owner), None)
        deck.owner.gold = 500

    return players, decks, games


def calculate_stats(players, decks, games):

    k_factor = 133
    d_factor = 200
    gold_ante = 25

    for game in games:

        winner_indx = game.decks.index(game.winner)
        new_deck_ratings = elo(k_factor, d_factor, [deck.rating for deck in game.decks], winner_indx)
        new_player_ratings = elo(k_factor, d_factor, [deck.owner.rating for deck in game.decks], winner_indx)

        for indx, deck in enumerate(game.decks):
            deck.rating = new_deck_ratings[indx]
            deck.owner.rating = new_player_ratings[indx]
            if indx == winner_indx:
                deck.wins += 1
                deck.owner.wins += 1
                deck.owner.gold += gold_ante *3
            else:
                deck.losses += 1
                deck.owner.losses += 1
                deck.owner.gold -= gold_ante

    # deck ratings
    active_decks = [x for x in decks if x.wins + x.losses > 0]
    for rank, deck in enumerate(sorted(active_decks, key=lambda x: x.rating, reverse=True)):
        print(f'{rank + 1} {deck.rating} {deck.commander} ({deck.owner.name}) {deck.wins}-{deck.losses}')

    # player's gold
    for rank, player in enumerate(sorted(players, key=lambda x: x.gold, reverse=True)):
        print(f'{rank + 1} {player.gold} {player.name} {player.wins}-{player.losses}')

    
def deck_stats(deck):
    """Returns basic stats like average cmc and total price of a deck"""

    # def card_price(card):
    #     values = [float(card.prices[key]) for key in ['usd', 'usd_foil', 'usd_etched'] 
    #               if card.prices[key] is not None]
    #     if values:
    #         return min(values)
    #     else:
    #         return 0

    count = 0
    cmc = 0
    # price = 0
    edhrec_rank = 0
    mana_symbols = [0, 0, 0, 0, 0] # WUBRG pip count
    for card in deck:
        if not card.type_line.startswith('Basic Land'):
            count += 1
            cmc += getattr(card, 'cmc', 0)
            # price += card_price(card)
            edhrec_rank += getattr(card, 'edhrec_rank', 0)
            # mana_symbols = [sum(x) for x in zip(mana_symbols, pips(card))]
            pips = [card.mana_cost.count(x) for x in ("{W}", "{U}", "{B}","{R}","{G}")]
            mana_symbols = [sum(x) for x in zip(mana_symbols, pips)]

    average_cmc = round(cmc/count, 2)
    edhrec_score = int(edhrec_rank/count)
    # total_price = int(price)

    return average_cmc, edhrec_score, mana_symbols


def process_decklists(decklists_directory='decklists', card_database='scryfall_data.json'):
    """Get moxfield decklists from directory and return card objects"""

    # Load scryfall card database
    cards = load_json_data(card_database, Card)

    decklists = []
    for file_name in os.listdir(decklists_directory):
        decklists.append({'name': file_name, 'cards': []})
        file_path = os.path.join(decklists_directory, file_name)
        with open(file_path) as f:
            for line in f:
                line = line.strip('\n')
                if line == 'SIDEBOARD:':
                    break
                if line != '':
                    split_line = line.strip().split(' ', 1)
                    qty = split_line[0]
                    card_name = split_line[1]
                    card_object = next((card for card in cards if card.name == card_name), None)
                    if card_object:
                        for _ in range(int(qty)):
                            decklists[-1]['cards'].append(card_object)

    return decklists


if __name__=='__main__':
    print('***Testing***')

    # # load data and print stats
    # players, decks, games = load_game_database()
    # calculate_stats(players, decks, games)
   

    stats = []
    for deck in process_decklists():
        cmc, edh_score, pips = deck_stats(deck['cards'])
        stats.append({'name': deck['name'],
                      'average_cmc': cmc,
                      'edh_score': edh_score,
                      'pips': pips})
        
    write_file(stats, 'stats.json')
        
    list_of_pips = [x['pips'] for x in stats]
    result = [sum(values) for values in zip(*(x['pips'] for x in stats))]
    print(result)

    # for i, v in enumerate(sorted(stats, key=lambda x: x['edh_score'], reverse=True)):
    #     print(f'{i+1}: {v}')

    # for i, v in enumerate(sorted(stats, key=lambda x: x['average_cmc'], reverse=True)):
    #     print(f'{i+1}: {v}')