import random
import string


class Deck():

  def __init__(self, name, weight):
    self.weight = weight
    self.wins = 0
    self.losses = 0


def simulate_game():
  """Randomly pick 4 decks and select a winner"""
  
  selected_decks = random.choices(decks, k=4)
  weights = [deck.weight for deck in selected_decks]

  winner = random.choices(selected_decks,
                          weights=weights,
                          k=1)

  # record win/loss
  for deck in selected_decks:
    if deck == winner[0]:
      deck.wins += 1
    else:
      deck.losses += 1

  return winner


decks = []
for letter in list(string.ascii_lowercase):
  decks.append(Deck(letter, random.randint(0, 50)))

for _ in range(50):
  simulate_game()

for deck in sorted(decks, key=lambda x: x.wins, reverse=True):
  print(deck.__dict__)
