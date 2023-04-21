def elo(k_factor: int, d_factor: int, ratings: list):
    '''Function takes two or more ratings, with the winner's rating first, and returns new ratings'''

    new_ratings = []
    for indx, rating in enumerate(ratings):
        # Basic elo equation is rating + k_factor * (1 - ev)
        new_ratings.append(round(rating + k_factor * ((indx == 0) - multi_ev(d_factor, ratings, indx))))

    return new_ratings


def multi_ev(d_factor: int, ratings: list, indx: int):
        '''returns a psudo average expected value of the indx rating against the others'''

        sum_ev = 0 
        for i, rating in enumerate(ratings):
            sum_ev += 1 / (1 + 10 ** ((rating - ratings[indx]) / d_factor)) if i != indx else 0

        return sum_ev / (len(ratings) * (len(ratings) - 1) / 2)

 
if __name__=='__main__':
    ratings = [1500,1600,1700,1800]
    new = elo(60,400,ratings)
    print(ratings)
    print(new)
    print([x - y for x, y in zip(new, ratings)])