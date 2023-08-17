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


def deck_stats(deck):
    """Returns basic stats like average cmc and total price of a deck"""

    def card_price(card):
        values = [float(card.prices[key]) for key in ['usd', 'usd_foil', 'usd_etched'] 
                  if card.prices[key] is not None]
        if values:
            return min(values)
        else:
            return 0
    
    basic_land_count = 0
    cmc = 0
    price = 0
    edhrec_rank = 0
    for card in deck:
        if card.type_line.startswith('Basic Land'):
            basic_land_count += 1
        else:
            cmc += card.cmc
            price += card_price(card)
            edhrec_rank += getattr(card, 'edhrec_rank', 0)

    return (f'Average cmc: {round(cmc/(len(deck) - basic_land_count), 2)}\n'
          f'EDHrec score: {int(edhrec_rank/(len(deck) - basic_land_count))}\n'
          f'Total price: {int(price)}')


def process_decklist(decklist_file, card_database):
    """Takes a moxfield decklist export and scryfall card data and returns a list of card objects"""
    path = os.path.join(os.path.dirname(__file__), decklist_file)
    decklist = []
    with open(path) as f:
        for line in f:
            decklist.append(line.strip().split(' ', 1)[1])
    return [card for card in card_database if card.name in decklist]


def roll(dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        return 'Format has to be in NdN!'

    return ', '.join(str(random.randint(1, limit)) for _ in range(rolls))


def scryfall_search(query, limit):
    # delay for scryfall API rate limit
    # time.sleep(0.05) 
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


if __name__=='__main__':
    print('***Testing***')

    players = load_json_data('players.json', Player)
    decks = load_json_data('decks.json', Deck)
    games = load_json_data('games.json', Game)
    print(f'Successfully loaded {len(players)} players, {len(decks)} decks, and {len(games)} games from the database.')

    # Load scryfall card database
    cards = load_json_data('scryfall_data.json', Card)

    # Print stats for each decklist
    decklists = ['grismold-3172023-20230729-165034.txt',
                  'dargo--jeska-20230803-163928.txt']
    for decklist_file in decklists:
        print(decklist_file)
        print(deck_stats(process_decklist(decklist_file, cards)))