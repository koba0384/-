
from __future__ import annotations

from .core import PlacedTile, TileInstance, get_board_bounds, player_color

CELL_SIZE = 74
SVG_SIZE = 64


def anchor_for_part(part: str) -> tuple[float, float]:
    anchors = {
        "N": (32, 11),
        "E": (53, 32),
        "S": (32, 53),
        "W": (11, 32),
        "C": (32, 32),
    }
    return anchors[part]


def average_anchor(parts: tuple[str, ...]) -> tuple[float, float]:
    coords = [anchor_for_part(part) for part in parts]
    x = sum(c[0] for c in coords) / len(coords)
    y = sum(c[1] for c in coords) / len(coords)
    return (x * 0.75 + 8, y * 0.75 + 8)


def road_svg(parts: tuple[str, ...]) -> str:
    segments = []
    for part in parts:
        x, y = anchor_for_part(part)
        segments.append(
            f'<line x1="32" y1="32" x2="{x}" y2="{y}" stroke="#e6c27a" stroke-width="14" stroke-linecap="round"/>'
        )
        segments.append(
            f'<line x1="32" y1="32" x2="{x}" y2="{y}" stroke="#8b6d3f" stroke-width="3" stroke-linecap="round"/>'
        )
    return "".join(segments)


def city_polygon(parts: tuple[str, ...]) -> str:
    parts_set = set(parts)
    if parts_set == {"N"}:
        return '<polygon points="0,0 64,0 44,28 20,28" fill="#9aa4b1"/>'
    if parts_set == {"E"}:
        return '<polygon points="64,0 64,64 36,44 36,20" fill="#9aa4b1"/>'
    if parts_set == {"S"}:
        return '<polygon points="0,64 64,64 44,36 20,36" fill="#9aa4b1"/>'
    if parts_set == {"W"}:
        return '<polygon points="0,0 28,20 28,44 0,64" fill="#9aa4b1"/>'
    if parts_set == {"N", "E"}:
        return '<polygon points="0,0 64,0 64,64 40,40 24,24" fill="#9aa4b1"/>'
    if parts_set == {"E", "S"}:
        return '<polygon points="64,0 64,64 0,64 24,40 40,24" fill="#9aa4b1"/>'
    if parts_set == {"S", "W"}:
        return '<polygon points="0,0 64,64 0,64 24,24 40,40" fill="#9aa4b1"/>'
    if parts_set == {"W", "N"}:
        return '<polygon points="0,0 64,0 40,24 24,40 0,64" fill="#9aa4b1"/>'
    if parts_set == {"N", "S"}:
        return '<polygon points="0,0 64,0 44,24 44,40 64,64 0,64 20,40 20,24" fill="#9aa4b1"/>'
    if parts_set == {"E", "W"}:
        return '<polygon points="0,0 64,20 64,44 0,64 20,40 44,40 44,24 20,24" fill="#9aa4b1"/>'
    if parts_set == {"N", "E", "S", "W"}:
        return '<polygon points="0,0 64,0 64,64 0,64" fill="#9aa4b1"/>'
    return '<polygon points="8,8 56,8 56,56 8,56" fill="#9aa4b1"/>'


def monastery_svg() -> str:
    return (
        '<g>'
        '<rect x="22" y="22" width="20" height="20" rx="2" fill="#c08b5c" stroke="#6d4c41" stroke-width="2"/>'
        '<polygon points="20,24 32,14 44,24" fill="#8d6e63" stroke="#6d4c41" stroke-width="2"/>'
        '<rect x="28" y="30" width="8" height="12" fill="#f7f2e8" stroke="#6d4c41" stroke-width="1"/>'
        '</g>'
    )


def meeple_marker_svg(placed: PlacedTile) -> str:
    pieces = []
    for region_id, player_index in placed.meeples.items():
        region = placed.tile.regions[region_id]
        x, y = average_anchor(region.parts)
        color = player_color(player_index)
        pieces.append(
            f'<g>'
            f'<circle cx="{x}" cy="{y}" r="8" fill="{color}" stroke="#222" stroke-width="1.5"/>'
            f'<text x="{x}" y="{y + 3}" font-size="8" text-anchor="middle" fill="white" font-family="Arial">M</text>'
            f'</g>'
        )
    return "".join(pieces)


def tile_svg(tile: TileInstance, meeple_tile: PlacedTile | None = None) -> str:
    layers = [
        '<rect x="0" y="0" width="64" height="64" rx="6" fill="#8fbc6c" stroke="#385723" stroke-width="2"/>'
    ]

    for region in tile.regions.values():
        if region.feature == "city":
            layers.append(city_polygon(region.parts))
        elif region.feature == "road":
            layers.append(road_svg(region.parts))
        elif region.feature == "monastery":
            layers.append(monastery_svg())

    layers.append(
        '<rect x="1.5" y="1.5" width="61" height="61" rx="6" fill="none" stroke="#ffffffaa" stroke-width="1"/>'
    )

    if meeple_tile is not None:
        layers.append(meeple_marker_svg(meeple_tile))

    return (
        f'<svg viewBox="0 0 64 64" width="{SVG_SIZE}" height="{SVG_SIZE}" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(layers)}</svg>'
    )


def html_for_tile(tile: TileInstance, placed: PlacedTile | None = None) -> str:
    return tile_svg(tile, placed)


def render_board_html(board: dict[tuple[int, int], PlacedTile]) -> str:
    min_x, max_x, min_y, max_y = get_board_bounds(board, padding=1)
    rows = []
    for y in range(min_y, max_y + 1):
        cells = []
        for x in range(min_x, max_x + 1):
            placed = board.get((x, y))
            if placed is None:
                content = '<div class="empty"></div>'
            else:
                content = html_for_tile(placed.tile, placed)
            cells.append(
                f'<div class="cell"><div class="coord">{x},{y}</div>{content}</div>'
            )
        rows.append(f'<div class="row">{"".join(cells)}</div>')

    return f"""
    <div class="board-wrapper">
      {"".join(rows)}
    </div>
    <style>
      .board-wrapper {{
        display: inline-flex;
        flex-direction: column;
        gap: 4px;
        padding: 8px;
        background: #f2eee4;
        border: 1px solid #d7ceb8;
        border-radius: 12px;
      }}
      .row {{
        display: flex;
        gap: 4px;
      }}
      .cell {{
        width: {CELL_SIZE}px;
        height: {CELL_SIZE + 14}px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        background: #fbfaf7;
        border: 1px solid #e1d9c8;
        border-radius: 10px;
        padding-top: 2px;
      }}
      .coord {{
        font-size: 10px;
        color: #5d5647;
        line-height: 12px;
      }}
      .empty {{
        width: {SVG_SIZE}px;
        height: {SVG_SIZE}px;
        border: 1px dashed #d4ccb8;
        border-radius: 8px;
        background: repeating-linear-gradient(
          45deg,
          #faf7f0,
          #faf7f0 6px,
          #f3eee4 6px,
          #f3eee4 12px
        );
      }}
    </style>
    """


def render_tile_card_html(tile: TileInstance) -> str:
    return f'<div style="display:flex;justify-content:center;padding:8px 0 4px 0;">{html_for_tile(tile)}</div>'
