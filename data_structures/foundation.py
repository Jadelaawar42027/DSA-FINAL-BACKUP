from data_structures.cards import Card

class FoundationPile:
    def __init__(self, suit: str):
        self.suit = suit  # H, D, C, or S
        self.cards = []  # stack (list)
    
    def can_add(self, card: Card) -> bool:
        # must be same suit
        if card.suit != self.suit:
            return False
        
        # if empty, must be Ace (rank 1)
        if len(self.cards) == 0:
            return card.rank == 1
        
        # otherwise, must be next rank in sequence
        return card.rank == self.cards[-1].rank + 1
    
    def add(self, card: Card) -> bool:
        if self.can_add(card):
            self.cards.append(card)
            return True
        return False
    
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
    
    def size(self) -> int:
        return len(self.cards)
