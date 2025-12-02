from data_structures.cards import Card


# The WastePile class is used to store the cards that are extracted 
# from the stock pile but are not played.
# The player can draw the top card that is revealed.
# Otherwise they have to go through the whole stock deck 
# before it gets flipped back to the stock

class WastePile:
    def __init__(self):
        self.cards = []  # stack (list)
    
    def add(self, card: Card):
        card.revealed = True  # cards in waste are always face-up
        self.cards.append(card)
    
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
    
    def is_empty(self) -> bool:
        return len(self.cards) == 0
    
    def size(self) -> int:
        return len(self.cards)
    
    def clear(self):
        # remove all cards (used when recycling waste to stock)
        self.cards.clear()
