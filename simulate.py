import random
import deckstats


if __name__ == '__main__':

  decks = deckstats.load_json_data('decks.json', deckstats.Deck)

  for _ in range(35):

    selected_decks = deckstats.random_decks(decks)
    winner = random.choice(selected_decks)
  
    for deck in selected_decks:
      if deck == winner:
        deck.wins += 1
      else:
        deck.losses += 1

  decks = [x for x in decks if x.wins + x.losses >= 3]
  for indx, deck in enumerate(sorted(decks, key=lambda x: x.wins/(x.wins + x.losses), reverse=True)):
    print(indx + 1, deck, deck.wins, deck.losses)