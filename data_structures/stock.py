from data_structures.cards import Card
from data_structures.waste import WastePile

class StockPile:
    def __init__(self):
        self.cards = []  # stack (list)
    
    def draw(self) -> Card:
        # remove and return top card
        if len(self.cards) > 0:
            return self.cards.pop()
        return None
    
    def add(self, card: Card):
        # add card to stock
        card.revealed = False  # cards in stock are face-down
        self.cards.append(card)
    
    def is_empty(self) -> bool:
        return len(self.cards) == 0
    
    def size(self) -> int:
        return len(self.cards)
    
    def recycle_waste(self, waste:WastePile):
        while len(waste.cards) > 0:
            waste_card = waste.cards.pop(0)
            waste_card.flip()
            self.cards.append(waste_card)

    def recycle_from(self, waste: WastePile):
        # Move all cards from waste back to stock, turning them face-down.
        # The typical solitaire behavior is to take the waste top and make it the top of stock.
        # Pop from the end of waste to preserve order when appended to stock.
        while len(waste.cards) > 0:
            card = waste.cards.pop()
            card.revealed = False
            self.cards.append(card)

        
