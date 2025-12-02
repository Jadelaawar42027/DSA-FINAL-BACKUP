import copy
import time

# this class represents a move in the game and provides a way to format moves
# as human-readable strings for display to the user
class Move:
    # this initializes a move with its type (like "board_to_board") and a dictionary
    # containing move-specific details like source column, destination column, and the card being moved
    # runtime complexity: worst case O(1), average case O(1)
    def __init__(self, move_type: str, details: dict):
        self.move_type = move_type
        self.details = details

    # this method formats the move as a human-readable string that describes what the move does
    # it handles different move types and formats them appropriately for display
    # runtime complexity: worst case O(1), average case O(1)
    def __str__(self):
        t = self.move_type
        d = self.details or {}
        # extract the card from details and convert it to a string representation
        # the card might be a card object, so we use repr to show its string representation
        card = d.get("card")
        card_str = repr(card) if card is not None else None

        # format different move types with appropriate descriptions
        if t == "board_to_board":
            return f"Move: {card_str} from column {d['from']} to column {d['to']}"
        if t == "board_to_foundation":
            return f"Move: {card_str} from column {d['from']} to the foundation"
        if t == "waste_to_board":
            return f"Move: {card_str} from waste to column {d['column']}"
        if t == "waste_to_foundation":
            return f"Move: {card_str} from waste to the foundation"
        if t == "draw_stock":
            return "Move: draw a card from the stock"
        if t == "reset_stock":
            return "Move: reset the stock"
        # fallback for unknown move types - show the type and all details
        if d:
            details_str = ", ".join(f"{k}={v}" for k, v in d.items())
            return f"Move: {t} ({details_str})"
        return f"Move: {t}"

    __repr__ = __str__


# this function converts the game state into a serialized tuple format
# it captures all the cards in the board, foundations, stock, and waste piles
# this serialized format is used to track visited states during the search algorithm
# to avoid exploring the same game state multiple times
# runtime complexity: worst case O(n), average case O(n)
# where n is the total number of cards (52)
def serialize_state(game):
    # serialize each board column as a tuple of (rank, suit, revealed) for each card
    # this preserves the order and state of cards in each column
    Board_ser = tuple(
        tuple((c.rank, c.suit, c.revealed) for c in pile.cards)
        for pile in game.Board
    )
    # serialize foundations for each suit (hearts, diamonds, clubs, spades)
    # foundations only need rank and suit since all cards are revealed
    foundation_ser = tuple(
        tuple((c.rank, c.suit) for c in game.foundations[suit].cards)
        for suit in ["H", "D", "C", "S"]
    )
    stock_ser = tuple((c.rank, c.suit) for c in game.stock.cards)
    waste_ser = tuple((c.rank, c.suit) for c in game.waste.cards)

    return (Board_ser, foundation_ser, stock_ser, waste_ser)


# this function calculates a numerical score for the current game state
# higher scores indicate better game positions that are closer to winning
# runtime complexity: worst case O(n), average case O(n)
# where n is the total number of cards (52)
def score_state(game):
    score = 0

    # award 10 points for each card successfully placed in a foundation pile
    # foundations are the goal of solitaire, so they are worth the most points
    for suit in ["H", "D", "C", "S"]:
        score += 10 * len(game.foundations[suit].cards)

    # award 2 points for each revealed card on the board
    for pile in game.Board:
        for card in pile.cards:
            if card.revealed:
                score += 2

    # award 3 points for each empty board column
    for pile in game.Board:
        if pile.size() == 0:
            score += 3

    return score


# used for validating card moves since solitaire requires alternating colors
# runtime complexity: worst case O(1), average case O(1)
def is_red(card):
    return card.suit in ["H", "D"]

# runtime complexity: worst case O(1), average case O(1)
def is_black(card):
    return card.suit in ["S", "C"]


# this function detects and prevents moves that would create a pattern of three consecutive
# cards of the same color (red-red-red or black-black-black)
# this prevents the algorithm from getting stuck in infinite loops where it moves cards
# back and forth between columns without making progress
# it only applies to board_to_board moves since those are the ones that can create oscillations
# runtime complexity: worst case O(1), average case O(1)
def illegal_color_repetition_move(game, move):
    # only check board_to_board moves since other moves cannot create oscillations
    if move.move_type != "board_to_board":
        return False

    src = move.details["from"]
    dst = move.details["to"]

    pile_src = game.Board[src]
    pile_dst = game.Board[dst]

    # if source pile is empty, the move is invalid anyway
    if pile_src.size() == 0:
        return False

    # get the card being moved (top card of source pile)
    moving_card = pile_src.peek()
    moving_is_red = is_red(moving_card)
    moving_is_black = is_black(moving_card)

    # check the destination card (the card the moving card will be placed on)
    # if destination is empty, the move is valid (no color conflict possible)
    if pile_dst.size() == 0:
        return False  # empty is fine

    dst_card = pile_dst.peek()
    dst_is_red = is_red(dst_card)
    dst_is_black = is_black(dst_card)

    # check the card beneath the moving card (the card that will be revealed)
    # we need at least 2 cards in source to have a card beneath
    if pile_src.size() >= 2:
        prev_card = pile_src.cards[-2]
        prev_is_red = is_red(prev_card)
        prev_is_black = is_black(prev_card)
    else:
        return False

    # block moves that would create three consecutive black cards
    # pattern: previous card (black) → moving card (black) → destination card (black)
    if moving_is_black and prev_is_black and dst_is_black:
        return True

    # block moves that would create three consecutive red cards
    # pattern: previous card (red) → moving card (red) → destination card (red)
    if moving_is_red and prev_is_red and dst_is_red:
        return True

    return False


# this function finds all legal moves available in the current game state
# it checks moves from the waste pile, board piles, and stock pile
# returns a list of Move objects representing all possible valid moves
# runtime complexity: worst case O(c² + m log m), average case O(c² + m log m)
# where c is the number of board columns (typically 7) and m is the number of legal moves
def get_legal_moves(game):
    moves = []

    # check moves from the waste pile (the top card of the waste pile can be moved)
    if game.waste.size() > 0:
        card = game.waste.peek()

        # check if the waste card can be moved to a foundation pile
        if game.foundations[card.suit].can_add(card):
            moves.append(Move("waste_to_foundation", {"card": card}))

        # check if the waste card can be moved to any board column
        for i, pile in enumerate(game.Board):
            if pile.can_add(card):
                moves.append(Move("waste_to_board", {"column": i, "card": card}))

    # check moves from board piles (each column's top card can potentially be moved)
    for i, pile in enumerate(game.Board):
        if pile.size() > 0:
            top = pile.peek()

            # check if the top card can be moved to its foundation pile
            if game.foundations[top.suit].can_add(top):
                moves.append(Move("board_to_foundation", {"from": i, "card": top}))

            # check if the top card can be moved to other board columns
            for j, dst in enumerate(game.Board):
                if i == j:
                    continue  # cannot move to the same column

                if dst.can_add(top):
                    moves.append(Move("board_to_board", {"from": i, "to": j, "card": top}))

    # check moves from the stock pile
    # if stock has cards, we can draw one
    if game.stock.size() > 0:
        moves.append(Move("draw_stock", {}))
    # if stock is empty but waste has cards, we can reset the stock
    elif game.waste.size() > 0:
        moves.append(Move("reset_stock", {}))

    return moves


# this function applies a move to a game state and returns a new game state
# it creates a deep copy of the game to avoid modifying the original game object
# after applying the move, it ensures that any newly revealed cards are marked as revealed
# runtime complexity: worst case O(n), average case O(n)
# where n is the total number of cards (52) due to deep copy operation
def apply_move(game, move):
    g = copy.deepcopy(game)

    if move.move_type == "draw_stock":
        g.waste.add(g.stock.draw())
        return g

    if move.move_type == "reset_stock":
        g.stock.recycle_from(g.waste)
        return g

    if move.move_type == "waste_to_foundation":
        c = g.waste.pop()
        g.foundations[c.suit].add(c)
        return g

    if move.move_type == "waste_to_board":
        c = g.waste.pop()
        g.Board[move.details["column"]].add(c)
        return g

    if move.move_type == "board_to_foundation":
        col = move.details["from"]
        c = g.Board[col].pop()
        g.foundations[c.suit].add(c)
        # after removing a card, reveal the new top card if the column is not empty
        if g.Board[col].size() > 0:
            # ensure top card is revealed
            try:
                g.Board[col].peek().revealed = True
            except Exception:
                # some pile implementations may not have peek(); be lenient
                if len(g.Board[col].cards) > 0:
                    g.Board[col].cards[-1].revealed = True
        return g

    if move.move_type == "board_to_board":
        src = move.details["from"]
        dst = move.details["to"]
        c = g.Board[src].pop()
        g.Board[dst].add(c)
        # after removing a card, reveal the new top card if the source column is not empty
        if g.Board[src].size() > 0:
            try:
                g.Board[src].peek().revealed = True
            except Exception:
                if len(g.Board[src].cards) > 0:
                    g.Board[src].cards[-1].revealed = True
        return g

    return g


# this function uses depth-first search (dfs) to explore possible game states
# and find the move that leads to the best game position
# it recursively explores moves up to a maximum depth, tracking visited states
# to avoid infinite loops, and returns the first move that leads to the highest score
# the algorithm prioritizes foundation moves, then board moves, then stock moves
# runtime complexity: worst case O(b^d * n), average case O(V * n)
# where b is the branching factor (average legal moves per state), d is max_depth (7),
# n is the total number of cards (52), and V is the number of unique visited states
# the visited set and depth limit prevent exponential explosion in practice
def find_best_move_tree(game, max_depth=7):
    start_time = time.time()
    # track visited game states to avoid exploring the same state multiple times
    visited = set()
    best_move = None
    best_score = -999999

    # mark the initial game state as visited
    visited.add(serialize_state(game))

    # recursive depth-first search function that explores game states
    def dfs(cur_game, depth, first_move):
        nonlocal best_move, best_score

        if depth >= max_depth:
            return

        moves = get_legal_moves(cur_game)

        # prioritize moves to explore better options first
        # foundation moves are most valuable (priority 0), then board moves (priority 1), then stock (priority 2)
        def move_priority(m):
            if "foundation" in m.move_type:
                return 0
            if "board" in m.move_type:
                return 1
            return 2

        moves.sort(key=move_priority)

        for move in moves:

            # block moves that would create same-color oscillations (infinite loops)
            if illegal_color_repetition_move(cur_game, move):
                continue

            new_game = apply_move(cur_game, move)
            key = serialize_state(new_game)
            if key in visited:
                continue

            visited.add(key)

            score = score_state(new_game)
            chosen = first_move if first_move else move

            if score > best_score:
                best_score = score
                best_move = chosen

            dfs(new_game, depth + 1, chosen)

    dfs(game, 0, None)

    # calculate how long the search took
    elapsed = (time.time() - start_time) * 1000

    if best_move is None:
        print(f"No move found | Computed in {elapsed:.0f}ms")
        return None
    else:
        move_str = str(best_move)
        print(f"Tree best move: {move_str} | Computed in {elapsed:.0f}ms")
        return move_str