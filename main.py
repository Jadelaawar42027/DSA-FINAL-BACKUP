
# These imports handle the prediction engines that power the hint functionality
from game_logic.best_move_tree import find_best_move_tree
from game_logic.best_move_graph import find_best_move_graph

# This is used to shuffle the card deck
from random import shuffle

# These are the data structures for the cards and the piles
from data_structures.cards import Card
from data_structures.foundation import FoundationPile
from data_structures.board import BoardPile
from data_structures.stock import StockPile
from data_structures.waste import WastePile

#constants
from config import RANKS, SUITS, BOARD_COLUMNS

# Imports for graphics
import pygame 
from ui import _Board_card_index_at_pos
from ui import *


# This is the class that will store the actual board data and which will 
# set up most of the initial game
class SolitaireGame:

    # This defines the piles in the board and deals cards to them
    def __init__(self):
        self.stock = StockPile()
        self.waste = WastePile()

        self.foundations = {
            "H": FoundationPile("H"),
            "D": FoundationPile("D"),
            "C": FoundationPile("C"),
            "S": FoundationPile("S")
        }

        self.Board = [BoardPile() for _ in range(BOARD_COLUMNS)]


        self.deal_cards()


    # This function creates a list of cards that will be later dealt across 
    # the board.
    def create_deck(self) -> list[Card]:
        deck = []
        for suit in SUITS:
            for rank in RANKS:
                deck.append(Card(rank, suit))
        shuffle(deck)
        return deck
    
    
    # This creates the deck from the previous function and deals the cards to all the piles on the board
    # it deals n cards to each board pile where n is the a number increasing from 1 to 8
    # It flips the top card over
    def deal_cards(self):
        deck = self.create_deck()
        deck_index = 0

        for i in range(BOARD_COLUMNS):
            for j in range(i + 1):
                card = deck[deck_index]
                card.revealed = (j == i)
                self.Board[i].cards.append(card)
                deck_index += 1

        for i in range(deck_index, len(deck)):
            self.stock.add(deck[i])





# This function determines what part of the board the user clicked on
def hit_test(layout: dict, pos, Board: list):
    x, y = pos
    if layout["stock"].collidepoint(x, y):
        return ("stock", -1, -1)
    if layout["waste"].collidepoint(x, y):
        return ("waste", -1, -1)
    for i, r in enumerate(layout["foundations"]):
        if r.collidepoint(x, y):
            return ("foundation", i, -1)
    for i, r in enumerate(layout["Board"]):
        # Build per-card rects to detect which card was clicked
        card_idx = _Board_card_index_at_pos(Board[i], r, pos)
        if card_idx != -1 or Rect(r.x, r.y, r.w, max(r.h, WINDOW_H - r.y - MARGIN)).collidepoint(x, y):
            return ("Board", i, card_idx)
    return ("none", -1, -1)




# This function ensures that the continuation of cards that is found in a pile is valid
def _is_valid_Board_sequence(pile: BoardPile, start_idx: int) -> bool:
    if start_idx < 0 or start_idx >= len(pile.cards):
        return False
    for i in range(start_idx, len(pile.cards)):
        if not pile.cards[i].revealed:
            return False
    for i in range(start_idx, len(pile.cards) - 1):
        a = pile.cards[i]
        b = pile.cards[i + 1]
        if a.rank != b.rank + 1:
            return False
        if a.is_red() == b.is_red():
            return False
    return True


# This function tries to run a user move from the selected source to the target
def attempt_move(game: SolitaireGame, selected: Dict[str, Any], target: Tuple[str, int]) -> bool:
    src_type = selected["type"]
    src_idx = selected.get("index", -1)
    dst_type, dst_idx = target

    if src_type == "waste" and game.waste.size() > 0:
        card = game.waste.peek()
        if dst_type == "foundation":
            suit_order = ["H", "D", "C", "S"]
            suit = suit_order[dst_idx]
            if game.foundations[suit].can_add(card):
                game.foundations[suit].add(game.waste.pop())
                return True
        if dst_type == "Board":
            if game.Board[dst_idx].can_add(card):
                game.Board[dst_idx].add(game.waste.pop())
                return True
        return False

    if src_type == "Board" and game.Board[src_idx].size() > 0:
        src_card_index = selected.get("card_index", len(game.Board[src_idx].cards) - 1)
        if not _is_valid_Board_sequence(game.Board[src_idx], src_card_index):
            return False
        moving_card = game.Board[src_idx].cards[src_card_index]
        if dst_type == "foundation":
            suit_order = ["H", "D", "C", "S"]
            suit = suit_order[dst_idx]
            if src_card_index == len(game.Board[src_idx].cards) - 1 and game.foundations[suit].can_add(moving_card):
                moved = game.Board[src_idx].pop()
                game.foundations[suit].add(moved)
                if game.Board[src_idx].size() > 0:
                    game.Board[src_idx].cards[-1].revealed = True
                return True
        if dst_type == "Board":
            if src_idx != dst_idx and game.Board[dst_idx].can_add(moving_card):
                run = game.Board[src_idx].cards[src_card_index:]
                del game.Board[src_idx].cards[src_card_index:]
                for c in run:
                    c.revealed = True
                    game.Board[dst_idx].add(c)
                if game.Board[src_idx].size() > 0:
                    game.Board[src_idx].cards[-1].revealed = True
                return True
        return False

    return False


# This is the main game loop that runs the actual 
# game until an end condition flips the running flag
if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("Solitaire (Pygame)")
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('arial', 24)
    font_small = pygame.font.SysFont('arial', 18)

    game = SolitaireGame()
    layout = build_layout(WINDOW_W, WINDOW_H)
    selected: Optional[Dict[str, Any]] = None
    best_suggestion = None
    show_suggestion_ms = 0
    button_message_tree = ""
    button_message_graph = ""

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                area, idx, card_idx = hit_test(layout, pos, game.Board)

                # Button click (bottom-right)
                if layout.get("button") and layout["button"].collidepoint(pos):
                    best_move_tree = find_best_move_tree(game)
                    button_message_tree = f"Tree: {best_move_tree}"
                    
                    best_move_graph = find_best_move_graph(game)
                    button_message_graph = f"Graph: {best_move_graph}"
                    continue

                if area == "stock":
                    drawn = game.stock.draw()
                    if drawn:
                        drawn.revealed = True
                        game.waste.add(drawn)
                        button_message_tree = ""
                        button_message_graph = ""
                    else:
                        if game.waste.size() > 0:
                            game.stock.recycle_from(game.waste)
                            button_message_tree = ""
                            button_message_graph = ""
                    selected = None
                    continue

                if selected:
                    moved = attempt_move(game, selected, (area, idx))
                    if moved:
                        selected = None
                        button_message_tree = ""
                        button_message_graph = ""
                        continue
                    if selected.get("type") == area and selected.get("index", -1) == idx and selected.get("card_index", -1) == card_idx:
                        selected = None
                        continue

                if area == "waste" and game.waste.size() > 0:
                    selected = {"type": "waste"}
                elif area == "Board" and game.Board[idx].size() > 0 and card_idx != -1 and game.Board[idx].cards[card_idx].revealed:
                    selected = {"type": "Board", "index": idx, "card_index": card_idx}
                else:
                    selected = None

        screen.fill(BACKGROUND_COLOR)

        mouse_pos = pygame.mouse.get_pos()
        button_hover = layout.get("button") and layout["button"].collidepoint(mouse_pos)

        draw_stock(screen, game.stock, layout["stock"], font_small, selected)
        draw_waste(screen, game.waste, layout["waste"], font, font_small, selected)
        draw_foundations(screen, game.foundations, layout["foundations"], font, font_small, selected)
        draw_Board(screen, game.Board, layout["Board"], font, font_small, selected)
        if layout.get("button"):
            draw_button(screen, layout["button"], "Show Hint", font_small, bool(button_hover))

        if button_message_graph:
            draw_text(screen, button_message_graph, (MARGIN, WINDOW_H - MARGIN - 20 - 22), font_small, (255, 255, 255))
        if button_message_tree:
            draw_text(screen, button_message_tree, (MARGIN, WINDOW_H - MARGIN - 40 - 22), font_small, (255, 255, 255))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit(0)
