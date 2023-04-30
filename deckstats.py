import json
import requests
from bs4 import BeautifulSoup
import config
import asyncio


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


def read_file(path):
    '''Read json data from a file'''
    with open(path, 'r') as f:
        data = json.load(f)
    return data


def write_file(data, path):
    '''Write json data to a file'''
    with open(path, 'w') as f:
        f.write(json.dumps(data, indent=4))


# def register_decks(decklist_links: dict):
#     commanders = {owner: [get_commander_name(link) for link in links] 
#                   for owner, links in decklist_links.items()}
#     # write new dict to file
#     path = f'{config.current_dir}\\decks.json'
#     write_file(commanders, path)
#     number_of_decks = sum(len(items) for items in commanders.values())
#     print(f'Saved {number_of_decks} decks to {path}')


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


if __name__=='__main__':
    # testing
    ratings = [1500,1600,1700,1800]
    print(elo(60,400,ratings,0))