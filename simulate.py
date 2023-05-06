import random
import deckstats


def random_decks(decks: list[object], players=None):
    """Returns a random decks for each player"""
    if players == None:
        players = random.sample(list(set([x.owner for x in decks])), k=4)

    return [random.choice([deck for deck in decks if deck.owner == player]) for player in players]


def simulate_game(decks: list[object]):
  """Randomly pick 4 decks and select a winner"""

  selected_decks = random_decks(decks)
  winner = random.choice(selected_decks)
  
  # record win/loss
  for deck in selected_decks:
    if deck == winner:
      deck.wins += 1
    else:
      deck.losses += 1


decks = deckstats.load_json_data('decks.json', deckstats.Deck)
for _ in range(100):
  simulate_game(decks)

for indx, deck in enumerate(sorted(decks, key=lambda x: x.wins, reverse=True)):
  print(indx + 1, deck, deck.wins, deck.losses)