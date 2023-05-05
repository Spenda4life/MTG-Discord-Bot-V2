import json
import requests
from bs4 import BeautifulSoup
import random
import os
import time


class Player:
    def __init__(self, name):
        self.name = name
        self.rating = 1500
        self.gold = 0
        self.wins = 0
        self.losses = 0


class Deck:
    def __init__(self, owner, commander, decklist, 
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


def register_game(date, winner, decks):
    """Wrtie new game to json file"""
    games = load_json_data('games.json', Game)
    new_game = Game(date,winner,decks)
    games.append(new_game)
    save_to_json(games,'games.json')
    return new_game


def load_json_data(file_name, cls):
    """Load json data to class objects"""
    path = f'{os.path.dirname(__file__)}\{file_name}'
    return [cls(**obj) for obj in read_file(path)]


def save_to_json(objects: list, file_name):
    """Save list of class objects to json file"""
    path = f'{os.path.dirname(__file__)}\{file_name}'
    write_file([deck.__dict__ for deck in objects], path)


def read_file(path):
    '''Read json data from a file'''
    with open(path, 'r') as f:
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
    
    soup = BeautifulSoup(response.text, 'html.parser')

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


def roll(dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        return 'Format has to be in NdN!'

    return ', '.join(str(random.randint(1, limit)) for _ in range(rolls))


# def scryfall_search(query, limit):
#     # delay for scryfall API rate limit
#     time.sleep(0.05) 
#     # Format text for query url and send the GET request
#     query.replace(' ', '+').replace(':', '%3A')
#     response = requests.get(f'https://api.scryfall.com/cards/search?q={query}')
#     response_json = response.json()
#     output = ''
#     for card in [card['id'] for card in response_json['data']][:limit]:
#         text = requests.get(f'https://api.scryfall.com/cards/{card}?format=text&pretty=true')
#         output += f'{text.text}\n\n'
#     return output[:2000]


if __name__=='__main__':
    print('***Testing***')

    decks = load_json_data('decks.json', Deck)
    games = load_json_data('games.json', Game)
    print(f'Successfully loaded {len(decks)} decks and {len(games)} games from database.')