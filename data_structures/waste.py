from data_structures.cards import Card

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
