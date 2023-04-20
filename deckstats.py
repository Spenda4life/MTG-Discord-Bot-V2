def elo(k_factor, d_factor, ratings):
    '''Function takes two or more ratings, with the winner's rating first, and returns new ratings'''

    def multi_ev(ratings):
        '''returns ev of the first rating against the others'''
        
        winner = ratings[0]
        num_players = len(ratings)
        possible_matchups = num_players * (num_players - 1) / 2

        # sum EVs for all possible 1v1 matchup with the first rating
        sum_ev = 0
        for loser in ratings[1:]:
            sum_ev += 1 / (1 + 10 ** ((loser - winner) / d_factor))

        # returns a quasi average ev
        return sum_ev / possible_matchups
    
    # This loop will iterate once for each rating in the list
    # The idea is to shuffle the list so each rating is first once
    new_ratings = []
    for i in range(len(ratings)):
        
        # Get ev for the first rating in the list
        ev = multi_ev(ratings)

        # first is for the winner, the rest are for the losers
        if i == 0:
            new = ratings[0] + round(k_factor * (1 - ev))
        else:
            new = ratings[0] + round(k_factor * (0 - ev))
            
        # add new rating to a list
        new_ratings.append(new)
        
        # move first rating to the end of the list for the next iteration
        ratings.append(ratings.pop(0))
    
    return new_ratings