# best_move_graph.py
import copy
import time
from collections import deque

# ---------------- MOVE CLASS (human-friendly printing) ----------------
class Move:
    def __init__(self, move_type: str, details: dict):
        self.move_type = move_type
        self.details = details

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

# ---------------- CANONICAL STATE SERIALIZATION ----------------
def serialize_state(game):
    board_cols = []
    for pile in game.Board:
        pile_ser = tuple((c.rank, c.suit, c.revealed) for c in pile.cards)
        board_cols.append(pile_ser)

    def top_key(col):
        if not col:
            return (-1, "Z", False)
        r, s, rev = col[-1]
        return (r, s, rev)

    board_ser = tuple(sorted(board_cols, key=top_key))
    foundation_ser = tuple(tuple((c.rank, c.suit) for c in game.foundations[s].cards) for s in ["H","D","C","S"])
    stock_ser = tuple((c.rank, c.suit) for c in game.stock.cards)
    waste_ser = tuple((c.rank, c.suit) for c in game.waste.cards)

    return (board_ser, foundation_ser, stock_ser, waste_ser)

# ---------------- SCORING ----------------
def score_state(game):
    score = 0
    for s in ["H","D","C","S"]:
        score += 10 * len(game.foundations[s].cards)
    for pile in game.Board:
        for c in pile.cards:
            if c.revealed:
                score += 3
    for pile in game.Board:
        if pile.size() == 0:
            score += 5
    return score

# ---------------- APPLY MOVE ----------------
def apply_move(game, move):
    g = copy.deepcopy(game)
    t = move.move_type
    d = move.details

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

# ---------------- LEGAL MOVES ----------------
def get_legal_moves(game):
    moves = []

    # waste moves
    if game.waste.size() > 0:
        card = game.waste.peek()
        if game.foundations[card.suit].can_add(card):
            moves.append(Move("waste_to_foundation", {"card": card}))
        for i, pile in enumerate(game.Board):
            if pile.can_add(card):
                moves.append(Move("waste_to_board", {"column": i, "card": card}))

    # board moves
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

    # stock moves
    if game.stock.size() > 0:
        moves.append(Move("draw_stock", {}))
    elif game.waste.size() > 0:
        moves.append(Move("reset_stock", {}))

    # prioritize: foundation first, board moves next, stock last
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

# ---------------- GRAPH BFS SEARCH (depth-limited) ----------------
def find_best_move_graph(game, max_depth=15):
    start_time = time.time()
    root_key = serialize_state(game)

    visited = {root_key}
    queue = deque([(game, 0, None)])  # (state, depth, first_move)

    best_move = None
    best_score = -float("inf")

    while queue:
        current, depth, first_move = queue.popleft()
        if depth >= max_depth:
            continue

        legal = get_legal_moves(current)
        if not legal:
            continue

        for mv in legal:
            new_state = apply_move(current, mv)
            key = serialize_state(new_state)

            if key in visited:
                continue

            visited.add(key)

            sc = score_state(new_state)
            primary = first_move if first_move else mv
            if sc > best_score:
                best_score = sc
                best_move = primary

            queue.append((new_state, depth + 1, primary))

    elapsed_ms = (time.time() - start_time) * 1000
    move_str = str(best_move) if best_move else "No move found"
    print(f"Graph best move: {move_str} | Computed in {elapsed_ms:.0f}ms")
    return move_str
