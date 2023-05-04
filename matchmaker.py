#given players in match, return random decks that are appropriately grouped based on one or more criteria
import random
import json

random_decks = []

with open("decks.json", "r") as read_file:
    decks = json.load(read_file)
#who playing
players = ['ostertoaster10','bonaparte jones','DrSull','Spenda4life']

for x in players:
    random_decks.append(random.choice([deck['commander'] for deck in decks if deck['owner'] == x]))

# for each shortlist of decks, pick a random item from each
print(random_decks)

#Check criteria
#ELO
#win streak
#Win record
#Time since last played

#option to re-randomize
