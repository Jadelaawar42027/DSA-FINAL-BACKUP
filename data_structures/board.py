from data_structures.cards import Card


# The BoardPile class is used to define the pile of cards that is played on the board
# It can be used by the player to store cards in a proper order.
# cards can be added to it as long as they follow the correct rank
# if the top card is not revealed it will be flipped

class BoardPile:
    def __init__(self):
        self.cards = []  
    
    def can_add(self, card: Card) -> bool:
        # if empty, can only add King (rank 13)
        if len(self.cards) == 0:
            return card.rank == 13
        
        # get the last revealed (face-up) card
        top_card = self._get_top_revealed_card()
        if top_card is None:
            return False
        
        # must be descending rank (one less than top card)
        if card.rank != top_card.rank - 1:
            return False
        
        # must alternate colors (red on black or black on red)
        return self._opposite_colors(card, top_card)
    
    def add(self, card: Card) -> bool:
        if self.can_add(card):
            card.revealed = True  # cards added to Board are face-up
            self.cards.append(card)
            return True
        return False
    
    def _get_top_revealed_card(self) -> Card:
        # get the last face-up card in the pile
        for i in range(len(self.cards) - 1, -1, -1):
            if self.cards[i].revealed:
                return self.cards[i]
        return None
    
    def _opposite_colors(self, card1: Card, card2: Card) -> bool:
        # check if cards are opposite colors
        return card1.is_red() != card2.is_red()
    
    def peek(self) -> Card:
        # look at top card without removing
        if len(self.cards) > 0:
            return self.cards[-1]
        return None
    
    def pop(self) -> Card:
        # remove and return top card
        if len(self.cards) > 0:
            return self.cards.pop()
        return None
    
    def reveal_top_card(self):
        # flip the top card face-up if it exists and is face-down
        if len(self.cards) > 0 and not self.cards[-1].revealed:
            self.cards[-1].revealed = True
    
    def size(self) -> int:
        return len(self.cards)
