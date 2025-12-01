import copy
import time

# ---------------------------------------------------------
# MOVE CLASS (human-friendly printing)
# ---------------------------------------------------------
class Move:
    def __init__(self, move_type: str, details: dict):
        self.move_type = move_type
        self.details = details

    def __str__(self):
        t = self.move_type
        d = self.details or {}
        # card might be an object — show repr if present, else raw
        card = d.get("card")
        card_str = repr(card) if card is not None else None

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
        # fallback
        if d:
            details_str = ", ".join(f"{k}={v}" for k, v in d.items())
            return f"Move: {t} ({details_str})"
        return f"Move: {t}"

    __repr__ = __str__


# ---------------------------------------------------------
# SERIALIZATION
# ---------------------------------------------------------
def serialize_state(game):
    Board_ser = tuple(
        tuple((c.rank, c.suit, c.revealed) for c in pile.cards)
        for pile in game.Board
    )
    foundation_ser = tuple(
        tuple((c.rank, c.suit) for c in game.foundations[suit].cards)
        for suit in ["H", "D", "C", "S"]
    )
    stock_ser = tuple((c.rank, c.suit) for c in game.stock.cards)
    waste_ser = tuple((c.rank, c.suit) for c in game.waste.cards)
    return (Board_ser, foundation_ser, stock_ser, waste_ser)


# ---------------------------------------------------------
# SCORING
# ---------------------------------------------------------
def score_state(game):
    score = 0

    for suit in ["H", "D", "C", "S"]:
        score += 10 * len(game.foundations[suit].cards)

    for pile in game.Board:
        for card in pile.cards:
            if card.revealed:
                score += 2

    for pile in game.Board:
        if pile.size() == 0:
            score += 3

    return score


# ---------------------------------------------------------
# COLOR HELPERS
# ---------------------------------------------------------
def is_red(card):
    return card.suit in ["H", "D"]

def is_black(card):
    return card.suit in ["S", "C"]


# ---------------------------------------------------------
# NEW RULE: prevent same-color oscillation
# ---------------------------------------------------------
def illegal_color_repetition_move(game, move):
    if move.move_type != "board_to_board":
        return False

    src = move.details["from"]
    dst = move.details["to"]

    pile_src = game.Board[src]
    pile_dst = game.Board[dst]

    if pile_src.size() == 0:
        return False

    moving_card = pile_src.peek()
    moving_is_red = is_red(moving_card)
    moving_is_black = is_black(moving_card)

    # Destination card
    if pile_dst.size() == 0:
        return False  # empty is fine

    dst_card = pile_dst.peek()
    dst_is_red = is_red(dst_card)
    dst_is_black = is_black(dst_card)

    # Card beneath the moving card
    if pile_src.size() >= 2:
        prev_card = pile_src.cards[-2]
        prev_is_red = is_red(prev_card)
        prev_is_black = is_black(prev_card)
    else:
        return False

    # Block black → black → black pattern
    if moving_is_black and prev_is_black and dst_is_black:
        return True

    # Block red → red → red pattern
    if moving_is_red and prev_is_red and dst_is_red:
        return True

    return False


# ---------------------------------------------------------
# GENERATE LEGAL MOVES
# ---------------------------------------------------------
def get_legal_moves(game):
    moves = []

    # Waste moves
    if game.waste.size() > 0:
        card = game.waste.peek()

        if game.foundations[card.suit].can_add(card):
            moves.append(Move("waste_to_foundation", {"card": card}))

        for i, pile in enumerate(game.Board):
            if pile.can_add(card):
                moves.append(Move("waste_to_board", {"column": i, "card": card}))

    # Board moves
    for i, pile in enumerate(game.Board):
        if pile.size() > 0:
            top = pile.peek()

            # To foundation
            if game.foundations[top.suit].can_add(top):
                moves.append(Move("board_to_foundation", {"from": i, "card": top}))

            # To other tableau piles
            for j, dst in enumerate(game.Board):
                if i == j:
                    continue

                if dst.can_add(top):
                    moves.append(Move("board_to_board", {"from": i, "to": j, "card": top}))

    # Stock moves
    if game.stock.size() > 0:
        moves.append(Move("draw_stock", {}))

    elif game.waste.size() > 0:
        moves.append(Move("reset_stock", {}))

    return moves


# ---------------------------------------------------------
# APPLY MOVE
# ---------------------------------------------------------
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
        if g.Board[src].size() > 0:
            try:
                g.Board[src].peek().revealed = True
            except Exception:
                if len(g.Board[src].cards) > 0:
                    g.Board[src].cards[-1].revealed = True
        return g

    return g


# ---------------------------------------------------------
# TREE SEARCH (DFS)
# ---------------------------------------------------------
def find_best_move_tree(game, max_depth=7):
    start_time = time.time()
    visited = set()
    best_move = None
    best_score = -999999

    visited.add(serialize_state(game))

    def dfs(cur_game, depth, first_move):
        nonlocal best_move, best_score

        if depth >= max_depth:
            return

        moves = get_legal_moves(cur_game)

        # Prioritize moves
        def move_priority(m):
            if "foundation" in m.move_type:
                return 0
            if "board" in m.move_type:
                return 1
            return 2

        moves.sort(key=move_priority)

        for move in moves:

            # NEW RULE: block same-color oscillations
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

    elapsed = (time.time() - start_time) * 1000

    if best_move is None:
        print(f"No move found | Computed in {elapsed:.0f}ms")
        return None
    else:
        move_str = str(best_move)
        print(f"Tree best move: {move_str} | Computed in {elapsed:.0f}ms")
        return move_str
