from flask import Flask, render_template, request, session
import random
# from collections import Counter
from utils.odds_calc import HoldemTable
import copy
import time
import os
import numpy as np

app = Flask(__name__)
app.secret_key = 'supersecretkey'

rank_map = {
    2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 
    10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'
}

suit_map = {
    0: 'd', 1: 'c', 2: 's', 3: 'h'  # Clubs, Diamonds, Hearts, Spades
}

def get_card_image(rank, suit):
    """Map the rank and suit to a card image filename."""
    rank_str = rank_map.get(rank)
    suit_str = suit_map.get(suit)
    return f"{rank_str}{suit_str}.png" if rank_str and suit_str else None

def calculate_odds(ht):
    n_sim = 30
    prob = {
        'win': 0,
        'tie': 0
    }
    for _ in range(n_sim):
        temp_ht = copy.deepcopy(ht)
        # temp_ht = HoldemTable(num_players=num_opponents+1, deck_type='full')
        # temp_ht.add_to_hand(1, player_cards)
        temp_ht.next_round()
        # if community_count == 3: temp_ht.next_round()
        temp = temp_ht.simulate(num_scenarios=10000)
        prob['win'] += (temp['Player 1 Win']/100)
        prob['tie'] += (temp['Player 1 Tie']/100)
    
    prob['win'] /= n_sim
    prob['tie'] /= n_sim

    return {
        'win': prob['win'],
        'lose': 1 - prob['win'] - prob['tie'],
        'tie': prob['tie']
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        num_players = np.random.randint(2, 10)
        ht = HoldemTable(num_players=num_players, deck_type='full')
        player_card = ht.random_card(2).tolist()
        ht.add_to_hand(1, player_card)
        community_card = None
        if np.random.random() < 0.66:
            community_card = ht.random_card(np.random.randint(3, 5)).tolist()
            ht.add_to_community(community_card)

        print(ht.view_table())

        # Map cards to image filenames
        player_hand_images = [get_card_image(card[0], card[1]) for card in player_card]
        if community_card:
            community_cards_images = [get_card_image(card[0], card[1]) for card in community_card]
        else:
            community_cards_images = None

        session['poker_data'] = {
            'player_hand': player_card,
            'community_cards': community_card,
            'num_opponents': num_players-1,
            'win_prob': None,
            'player_hand_images': player_hand_images,
            'community_cards_images': community_cards_images
        }

        return render_template('index.html', poker_data=session['poker_data'])

    elif request.method == 'POST':
        # Retrieve poker data from session
        poker_data = session.get('poker_data')
        if not poker_data:
            return render_template('index.html', error="Session expired. Refresh to start a new game.")


        player_card = np.array(poker_data['player_hand'])
        community_card = poker_data['community_cards']
        num_opponents = poker_data['num_opponents']

        ht = HoldemTable(num_players=num_opponents+1, deck_type="full")
        ht.add_to_hand(1, player_card)
        if community_card: ht.add_to_community(np.array(community_card))

        win_rate = calculate_odds(ht)['win']
        # rounded_win_rate = round(win_rate, 1)
        print(ht.view_table())
        poker_data['win_prob'] = win_rate

        # Get user predictions
        try:
            predicted_win = float(request.form['predicted_win'])
        except ValueError:
            return render_template('index.html', error="Please enter valid probabilities.", poker_data=poker_data)

        # Calculate errors
        win_error = abs(predicted_win - win_rate)

        return render_template('index.html', 
                               poker_data=poker_data, 
                               predicted_win=predicted_win,
                               win_error=win_error)

if __name__ == '__main__':
    app.run(debug=True)
