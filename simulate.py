import random
import deckstats


if __name__ == '__main__':

  decks = deckstats.load_json_data('decks.json', deckstats.Deck)

  for _ in range(100):

    selected_decks = deckstats.random_decks(decks)
    winner = random.choice(selected_decks)
  
    for deck in selected_decks:
      if deck == winner:
        deck.wins += 1
      else:
        deck.losses += 1

  for indx, deck in enumerate(sorted(decks, key=lambda x: x.wins, reverse=True)):
    print(indx + 1, deck, deck.wins, deck.losses)