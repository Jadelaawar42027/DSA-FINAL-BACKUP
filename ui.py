import sys
import pygame
from pygame import Rect, Surface
from typing import Optional, Dict, Any, Tuple, List

from config import RANK_NAMES, SUIT_SYMBOLS, SUIT_COLORS, BOARD_COLUMNS
from data_structures.foundation import FoundationPile
from data_structures.board import BoardPile
from data_structures.stock import StockPile
from data_structures.waste import WastePile
from data_structures.cards import Card


# Window and layout constants
WINDOW_W, WINDOW_H = 1024, 768
CARD_W, CARD_H = 88, 120
MARGIN = 24
TOP_GAP_X = 16
ROW_GAP_Y = 32
SPREAD_FACEUP_Y = 28
SPREAD_FACEDOWN_Y = 16

BACKGROUND_COLOR = (7, 99, 36)  # green felt
CARD_FACE_COLOR = (255, 255, 255)
CARD_BACK_COLOR = (40, 100, 200)
CARD_BORDER_COLOR = (20, 20, 20)
SLOT_COLOR = (0, 0, 0)
SELECT_COLOR = (255, 200, 0)
LABEL_COLOR = (230, 230, 230)

# Button constants
BUTTON_W, BUTTON_H = 160, 40
BUTTON_BG = (50, 50, 50)
BUTTON_BG_HOVER = (70, 70, 70)
BUTTON_TEXT = (240, 240, 240)

# UI
def build_layout(window_w: int, window_h: int) -> Dict[str, Any]:
    top_y = MARGIN

    stock_rect = Rect(MARGIN, top_y, CARD_W, CARD_H)
    waste_rect = Rect(stock_rect.right + TOP_GAP_X, top_y, CARD_W, CARD_H)

    f_gap = TOP_GAP_X
    total_f_width = 4 * CARD_W + 3 * f_gap
    start_fx = window_w - MARGIN - total_f_width
    foundation_rects = [
        Rect(start_fx + i * (CARD_W + f_gap), top_y, CARD_W, CARD_H) for i in range(4)
    ]

    Board_y = top_y + CARD_H + ROW_GAP_Y
    usable_w = window_w - 2 * MARGIN - 7 * CARD_W
    col_gap = max(8, usable_w // 6)  # 6 gaps between 7 columns
    Board_rects = [
        Rect(MARGIN + i * (CARD_W + col_gap), Board_y, CARD_W, CARD_H)
        for i in range(BOARD_COLUMNS)
    ]

    # Bottom-right button
    button_rect = Rect(
        window_w - MARGIN - BUTTON_W,
        window_h - MARGIN - BUTTON_H,
        BUTTON_W,
        BUTTON_H,
    )

    return {
        "stock": stock_rect,
        "waste": waste_rect,
        "foundations": foundation_rects,
        "Board": Board_rects,
        "button": button_rect,
    }

# UI
def draw_text(surface: Surface, text: str, pos: Tuple[int, int], font: pygame.font.Font, color=(0, 0, 0)):
    img = font.render(text, True, color)
    surface.blit(img, pos)

def draw_button(surface: Surface, rect: Rect, label: str, font: pygame.font.Font, hovered: bool = False):
    bg = BUTTON_BG_HOVER if hovered else BUTTON_BG
    pygame.draw.rect(surface, bg, rect, border_radius=8)
    pygame.draw.rect(surface, (200, 200, 200), rect, width=2, border_radius=8)
    text_img = font.render(label, True, BUTTON_TEXT)
    tx = rect.x + (rect.w - text_img.get_width()) // 2
    ty = rect.y + (rect.h - text_img.get_height()) // 2
    surface.blit(text_img, (tx, ty))


# UI
def draw_card(surface: Surface, card: Card, x: int, y: int, font: pygame.font.Font):
    rect = Rect(x, y, CARD_W, CARD_H)
    pygame.draw.rect(surface, CARD_BORDER_COLOR, rect, border_radius=8)
    inner = rect.inflate(-4, -4)
    if card.revealed:
        pygame.draw.rect(surface, CARD_FACE_COLOR, inner, border_radius=6)
        suit_color = (220, 20, 60) if SUIT_COLORS[card.suit] == "red" else (10, 10, 10)
        rank = RANK_NAMES[card.rank]
        suit = SUIT_SYMBOLS[card.suit]
        draw_text(surface, f"{rank}{suit}", (inner.x + 8, inner.y + 6), font, suit_color)
        # mirrored corner
        text_img = font.render(f"{rank}{suit}", True, suit_color)
        surface.blit(text_img, (inner.right - text_img.get_width() - 8, inner.bottom - text_img.get_height() - 6))
    else:
        pygame.draw.rect(surface, CARD_BACK_COLOR, inner, border_radius=6)


# UI
def draw_slot(surface: Surface, rect: Rect):
    pygame.draw.rect(surface, SLOT_COLOR, rect, width=2, border_radius=8)


# UI
def draw_pile_label(surface: Surface, rect: Rect, label: str, font_small: pygame.font.Font):
    draw_text(surface, label, (rect.x, rect.bottom + 6), font_small, LABEL_COLOR)


# UI
def draw_stock(surface: Surface, stock: StockPile, rect: Rect, font_small: pygame.font.Font, selected: Optional[Dict[str, Any]]):
    if stock.size() > 0:
        # draw back of card
        draw_card(surface, Card(1, "S", revealed=False), rect.x, rect.y, font_small)
    else:
        draw_slot(surface, rect)
    draw_pile_label(surface, rect, "STOCK", font_small)
    if selected and selected.get("type") == "stock":
        pygame.draw.rect(surface, SELECT_COLOR, rect, width=3, border_radius=8)


# UI
def draw_waste(surface: Surface, waste: WastePile, rect: Rect, font: pygame.font.Font, font_small: pygame.font.Font, selected: Optional[Dict[str, Any]]):
    if waste.size() > 0:
        draw_card(surface, waste.peek(), rect.x, rect.y, font)
    else:
        draw_slot(surface, rect)
    draw_pile_label(surface, rect, "WASTE", font_small)
    if selected and selected.get("type") == "waste":
        pygame.draw.rect(surface, SELECT_COLOR, rect, width=3, border_radius=8)


# UI
def draw_foundations(surface: Surface, foundations: Dict[str, FoundationPile], rects: List[Rect], font: pygame.font.Font, font_small: pygame.font.Font, selected: Optional[Dict[str, Any]]):
    suits = ["H", "D", "C", "S"]
    for i, suit in enumerate(suits):
        rect = rects[i]
        pile = foundations[suit]
        if pile.size() > 0:
            draw_card(surface, pile.peek(), rect.x, rect.y, font)
        else:
            draw_slot(surface, rect)
        draw_pile_label(surface, rect, f"FND {SUIT_SYMBOLS[suit]}", font_small)
        if selected and selected.get("type") == "foundation" and selected.get("index") == i:
            pygame.draw.rect(surface, SELECT_COLOR, rect, width=3, border_radius=8)


# UI
def draw_Board(surface: Surface, Board: List[BoardPile], rects: List[Rect], font: pygame.font.Font, font_small: pygame.font.Font, selected: Optional[Dict[str, Any]]):
    for i, pile in enumerate(Board):
        base = rects[i]
        label_rect = Rect(base.x - 30, base.y, 25, 20)
        draw_text(surface, f"T{i}", (label_rect.x, label_rect.y), font_small, LABEL_COLOR)
        if pile.size() == 0:
            draw_slot(surface, base)
            if selected and selected.get("type") == "Board" and selected.get("index") == i:
                pygame.draw.rect(surface, SELECT_COLOR, base, width=3, border_radius=8)
            continue
        y = base.y
        last_card_y = y
        for c in pile.cards:
            last_card_y = y
            draw_card(surface, c, base.x, y, font)
            y += SPREAD_FACEUP_Y if c.revealed else SPREAD_FACEDOWN_Y
        if selected and selected.get("type") == "Board" and selected.get("index") == i:
            bottom_card_rect = Rect(base.x, last_card_y, CARD_W, CARD_H)
            pygame.draw.rect(surface, SELECT_COLOR, bottom_card_rect, width=3, border_radius=8)


# UI
def _Board_card_index_at_pos(pile: BoardPile, base: Rect, pos: Tuple[int, int]) -> int:
    # Return the index of the clicked card within the pile, or -1 if none.
    x, y = pos
    cur_y = base.y
    for i, c in enumerate(pile.cards):
        # Non-top cards expose only a strip; top card exposes full height
        h = CARD_H if i == len(pile.cards) - 1 else (SPREAD_FACEUP_Y if c.revealed else SPREAD_FACEDOWN_Y)
        rect = Rect(base.x, cur_y, CARD_W, max(h, 8))
        if rect.collidepoint(x, y):
            return i
        cur_y += SPREAD_FACEUP_Y if c.revealed else SPREAD_FACEDOWN_Y
    return -1






