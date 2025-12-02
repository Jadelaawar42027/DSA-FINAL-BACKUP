# used for copying game states, timing, and queue operations
import copy
import time
from collections import deque

# class to represent a move in the game and formats it for display
class Move:
    # initializes a move with its type and details
    # runtime complexity: worst case O(1), average case O(1)
    def __init__(self, move_type: str, details: dict):
        self.move_type = move_type
        self.details = details

    # this formats the move as a human-readable string (used in console and UI)
    # runtime complexity: worst case O(1), average case O(1)
    def __str__(self):
        t = self.move_type
        d = self.details
        if t == "board_to_board":
            return f"Move: {d.get('card')} from column {d['from']} to column {d['to']}"
        if t == "board_to_foundation":
            return f"Move: {d.get('card')} from column {d['from']} to the foundation"
        if t == "waste_to_board":
            return f"Move: {d.get('card')} from waste to column {d['column']}"
        if t == "waste_to_foundation":
            return f"Move: {d.get('card')} from waste to the foundation"
        if t == "draw_stock":
            return "Move: draw a card from the stock"
        if t == "reset_stock":
            return "Move: reset the stock"
        return f"Move: {t} {d}"

    __repr__ = __str__

# this function converts the game state into a tuple structure so that the game state is consistent regardless of the column order
# it sorts board columns by their top card to ensure consistent state representation
# runtime complexity: worst case O(n + c log c), average case O(n + c log c)
# where n is the total number of cards (52) and c is the number of board columns (typically 7)
# simplifies to O(n) since n dominates c log c
def serialize_state(game):
    board_cols = []
    # get the cards in each board column
    for pile in game.Board:
        pile_ser = tuple((c.rank, c.suit, c.revealed) for c in pile.cards)
        board_cols.append(pile_ser)

    # this helper function returns a key for sorting columns by their top card
    def top_key(col):
        if not col:
            return (-1, "Z", False)
        r, s, rev = col[-1]
        return (r, s, rev)

    # sorts board columns by their top card
    board_ser = tuple(sorted(board_cols, key=top_key))
    foundation_ser = tuple(tuple((c.rank, c.suit) for c in game.foundations[s].cards) for s in ["H","D","C","S"])
    stock_ser = tuple((c.rank, c.suit) for c in game.stock.cards)
    waste_ser = tuple((c.rank, c.suit) for c in game.waste.cards)

    return (board_ser, foundation_ser, stock_ser, waste_ser)

# this function calculates a score for the current game state
# higher scores indicate better game positions
# runtime complexity: worst case O(n), average case O(n)
# where n is the total number of cards (52)
def score_state(game):
    score = 0
    # add points for cards in foundations
    for s in ["H","D","C","S"]:
        score += 10 * len(game.foundations[s].cards)
    # add points for revealed cards on the board
    for pile in game.Board:
        for c in pile.cards:
            if c.revealed:
                score += 3
    # add points for empty board columns
    for pile in game.Board:
        if pile.size() == 0:
            score += 5
    return score

# this function applies a move to a game state and returns a new game state
# it creates a deep copy to avoid modifying the original game
# runtime complexity: worst case O(n), average case O(n)
# where n is the total number of cards (52) due to deep copy operation
def apply_move(game, move):
    g = copy.deepcopy(game)
    t = move.move_type
    d = move.details

    # handles different move types
    if t == "draw_stock":
        g.waste.add(g.stock.draw())
        return g
    if t == "reset_stock":
        g.stock.recycle_from(g.waste)
        return g
    if t == "waste_to_foundation":
        card = g.waste.pop()
        g.foundations[card.suit].add(card)
        return g
    if t == "waste_to_board":
        card = g.waste.pop()
        g.Board[d["column"]].add(card)
        return g
    if t == "board_to_foundation":
        col = d["from"]
        card = g.Board[col].pop()
        g.foundations[card.suit].add(card)
        if g.Board[col].size() > 0:
            g.Board[col].cards[-1].revealed = True
        return g
    if t == "board_to_board":
        src = d["from"]
        dst = d["to"]
        card = g.Board[src].pop()
        g.Board[dst].add(card)
        if g.Board[src].size() > 0:
            g.Board[src].cards[-1].revealed = True
        return g
    return g

# this function finds all legal moves available in the current game state
# it returns moves sorted by priority (foundation moves first, then board moves, then stock)
# runtime complexity: worst case O(c² + m log m), average case O(c² + m log m)
# where c is the number of board columns (typically 7) and m is the number of legal moves
def get_legal_moves(game):
    moves = []

    # check moves from waste pile
    if game.waste.size() > 0:
        card = game.waste.peek()
        if game.foundations[card.suit].can_add(card):
            moves.append(Move("waste_to_foundation", {"card": card}))
        for i, pile in enumerate(game.Board):
            if pile.can_add(card):
                moves.append(Move("waste_to_board", {"column": i, "card": card}))

    # check moves from board piles
    for i, pile in enumerate(game.Board):
        if pile.size() == 0:
            continue
        card = pile.peek()
        if game.foundations[card.suit].can_add(card):
            moves.append(Move("board_to_foundation", {"from": i, "card": card}))
        for j, dst in enumerate(game.Board):
            if i == j:
                continue
            if dst.can_add(card):
                moves.append(Move("board_to_board", {"from": i, "to": j, "card": card}))

    # check moves from stock pile
    if game.stock.size() > 0:
        moves.append(Move("draw_stock", {}))
    elif game.waste.size() > 0:
        moves.append(Move("reset_stock", {}))

    # this helper function assigns priority to moves for sorting
    # foundation moves get highest priority, then board moves, then stock
    def priority(m):
        if m.move_type in ("waste_to_foundation", "board_to_foundation"):
            return 3
        if m.move_type in ("board_to_board", "waste_to_board"):
            return 2
        if m.move_type == "draw_stock":
            return 1
        return 0

    moves.sort(key=priority, reverse=True)
    return moves

# this function uses breadth-first search to find the best move
# it explores game states up to a maximum depth and returns the move leading to the highest score
# runtime complexity: worst case O(b^d * n), average case O(V * n)
# where b is the branching factor (average legal moves per state), d is max_depth (15),
# n is the total number of cards (52), and V is the number of unique visited states
# the visited set prevents exponential explosion in practice
def find_best_move_graph(game, max_depth=15):
    start_time = time.time()
    root_key = serialize_state(game)

    # track visited states to avoid cycles
    visited = {root_key}
    # queue stores (state, depth, first_move) tuples
    queue = deque([(game, 0, None)])

    best_move = None
    best_score = -float("inf")

    # use a queue to explore game states
    while queue:
        current, depth, first_move = queue.popleft()
        # skip states beyond maximum depth
        if depth >= max_depth:
            continue

        legal = get_legal_moves(current)
        # skip states with no legal moves
        if not legal:
            continue

        # explore all legal moves from current state
        for mv in legal:
            new_state = apply_move(current, mv)
            key = serialize_state(new_state)

            # skip already visited states
            if key in visited:
                continue

            visited.add(key)

            # evaluate the new state and update best move if needed
            sc = score_state(new_state)
            primary = first_move if first_move else mv
            if sc > best_score:
                best_score = sc
                best_move = primary

            # add new state to queue for further exploration
            queue.append((new_state, depth + 1, primary))

    # format and return the result
    elapsed_ms = (time.time() - start_time) * 1000
    move_str = str(best_move) if best_move else "No move found"
    print(f"Graph best move: {move_str} | Computed in {elapsed_ms:.0f}ms")
    return move_str