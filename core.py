
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random

DIRS = {
    "N": (0, -1),
    "E": (1, 0),
    "S": (0, 1),
    "W": (-1, 0),
}
OPPOSITE = {"N": "S", "E": "W", "S": "N", "W": "E"}
ROTATE_PART = {"N": "E", "E": "S", "S": "W", "W": "N", "C": "C"}

FEATURE_LABELS = {
    "city": "都市",
    "road": "道",
    "monastery": "修道院",
    "field": "草地",
}


@dataclass(frozen=True)
class RegionDef:
    id: str
    feature: str
    parts: Tuple[str, ...]


@dataclass(frozen=True)
class TileTemplate:
    code: str
    name: str
    edges: Dict[str, str]
    regions: Tuple[RegionDef, ...]
    count: int = 1
    starter: bool = False


@dataclass(frozen=True)
class RegionInstance:
    id: str
    feature: str
    parts: Tuple[str, ...]


@dataclass(frozen=True)
class TileInstance:
    template_code: str
    name: str
    edges: Dict[str, str]
    regions: Dict[str, RegionInstance]
    rotation: int


@dataclass
class PlacedTile:
    tile: TileInstance
    x: int
    y: int
    meeples: Dict[str, int] = field(default_factory=dict)

    @property
    def edge_to_region(self) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        for region_id, region in self.tile.regions.items():
            if region.feature not in {"road", "city"}:
                continue
            for part in region.parts:
                if part in DIRS:
                    mapping[part] = region_id
        return mapping


@dataclass
class PlayerState:
    name: str
    score: int = 0
    meeples_available: int = 7


@dataclass
class GameState:
    board: Dict[Tuple[int, int], PlacedTile]
    deck: List[TileTemplate]
    discarded_tiles: List[str]
    players: List[PlayerState]
    current_player: int
    current_tile: Optional[TileTemplate]
    turn: int
    log: List[str]
    winner_text: str = ""
    final_scored: bool = False

    def active_player(self) -> PlayerState:
        return self.players[self.current_player]


def rotate_edges(edges: Dict[str, str], steps: int) -> Dict[str, str]:
    steps %= 4
    new_edges = dict(edges)
    for _ in range(steps):
        new_edges = {
            "N": new_edges["W"],
            "E": new_edges["N"],
            "S": new_edges["E"],
            "W": new_edges["S"],
        }
    return new_edges


def rotate_parts(parts: Tuple[str, ...], steps: int) -> Tuple[str, ...]:
    steps %= 4
    rotated = list(parts)
    for _ in range(steps):
        rotated = [ROTATE_PART[p] for p in rotated]
    order = {"N": 0, "E": 1, "S": 2, "W": 3, "C": 4}
    return tuple(sorted(rotated, key=lambda p: order[p]))


def instantiate_tile(template: TileTemplate, rotation: int = 0) -> TileInstance:
    edges = rotate_edges(template.edges, rotation)
    regions = {
        region.id: RegionInstance(
            id=region.id,
            feature=region.feature,
            parts=rotate_parts(region.parts, rotation),
        )
        for region in template.regions
    }
    return TileInstance(
        template_code=template.code,
        name=template.name,
        edges=edges,
        regions=regions,
        rotation=rotation % 4,
    )


def build_tile_library() -> Dict[str, TileTemplate]:
    tiles = [
        TileTemplate(
            code="start_city_road",
            name="開始タイル",
            edges={"N": "city", "E": "field", "S": "road", "W": "field"},
            regions=(
                RegionDef("city_a", "city", ("N",)),
                RegionDef("road_a", "road", ("S",)),
            ),
            count=1,
            starter=True,
        ),
        TileTemplate(
            code="road_straight",
            name="直線の道",
            edges={"N": "road", "E": "field", "S": "road", "W": "field"},
            regions=(RegionDef("road_a", "road", ("N", "S")),),
            count=4,
        ),
        TileTemplate(
            code="road_curve",
            name="カーブの道",
            edges={"N": "road", "E": "road", "S": "field", "W": "field"},
            regions=(RegionDef("road_a", "road", ("N", "E")),),
            count=6,
        ),
        TileTemplate(
            code="road_t",
            name="三叉路",
            edges={"N": "road", "E": "road", "S": "road", "W": "field"},
            regions=(RegionDef("road_a", "road", ("N", "E", "S")),),
            count=3,
        ),
        TileTemplate(
            code="road_cross",
            name="十字路",
            edges={"N": "road", "E": "road", "S": "road", "W": "road"},
            regions=(RegionDef("road_a", "road", ("N", "E", "S", "W")),),
            count=2,
        ),
        TileTemplate(
            code="monastery_plain",
            name="修道院",
            edges={"N": "field", "E": "field", "S": "field", "W": "field"},
            regions=(RegionDef("monastery", "monastery", ("C",)),),
            count=3,
        ),
        TileTemplate(
            code="monastery_road",
            name="修道院と道",
            edges={"N": "road", "E": "field", "S": "field", "W": "field"},
            regions=(
                RegionDef("monastery", "monastery", ("C",)),
                RegionDef("road_a", "road", ("N",)),
            ),
            count=2,
        ),
        TileTemplate(
            code="city_cap",
            name="都市の先端",
            edges={"N": "city", "E": "field", "S": "field", "W": "field"},
            regions=(RegionDef("city_a", "city", ("N",)),),
            count=5,
        ),
        TileTemplate(
            code="city_cap_road",
            name="都市先端と道",
            edges={"N": "city", "E": "field", "S": "road", "W": "field"},
            regions=(
                RegionDef("city_a", "city", ("N",)),
                RegionDef("road_a", "road", ("S",)),
            ),
            count=4,
        ),
        TileTemplate(
            code="city_corner",
            name="都市の角",
            edges={"N": "city", "E": "city", "S": "field", "W": "field"},
            regions=(RegionDef("city_a", "city", ("N", "E")),),
            count=4,
        ),
        TileTemplate(
            code="city_corner_road",
            name="都市角と道",
            edges={"N": "city", "E": "city", "S": "road", "W": "field"},
            regions=(
                RegionDef("city_a", "city", ("N", "E")),
                RegionDef("road_a", "road", ("S",)),
            ),
            count=2,
        ),
        TileTemplate(
            code="double_city",
            name="向かい合う都市",
            edges={"N": "city", "E": "field", "S": "city", "W": "field"},
            regions=(
                RegionDef("city_n", "city", ("N",)),
                RegionDef("city_s", "city", ("S",)),
            ),
            count=3,
        ),
        TileTemplate(
            code="city_gate",
            name="都市と曲がる道",
            edges={"N": "city", "E": "road", "S": "road", "W": "field"},
            regions=(
                RegionDef("city_a", "city", ("N",)),
                RegionDef("road_a", "road", ("E", "S")),
            ),
            count=3,
        ),
        TileTemplate(
            code="city_full",
            name="大都市",
            edges={"N": "city", "E": "city", "S": "city", "W": "city"},
            regions=(RegionDef("city_a", "city", ("N", "E", "S", "W")),),
            count=1,
        ),
    ]
    return {tile.code: tile for tile in tiles}


def build_deck(tile_library: Optional[Dict[str, TileTemplate]] = None) -> Tuple[TileTemplate, List[TileTemplate]]:
    lib = tile_library or build_tile_library()
    starter = next(tile for tile in lib.values() if tile.starter)
    deck: List[TileTemplate] = []
    for tile in lib.values():
        if tile.starter:
            continue
        deck.extend([tile] * tile.count)
    return starter, deck


def new_game(num_players: int = 2, seed: Optional[int] = None) -> GameState:
    starter, deck = build_deck()
    rng = random.Random(seed)
    rng.shuffle(deck)
    players = [PlayerState(name=f"P{i+1}") for i in range(num_players)]
    starter_tile = instantiate_tile(starter, 0)
    board = {(0, 0): PlacedTile(tile=starter_tile, x=0, y=0)}
    log = ["ゲーム開始。開始タイルを (0, 0) に配置しました。"]
    state = GameState(
        board=board,
        deck=deck,
        discarded_tiles=[],
        players=players,
        current_player=0,
        current_tile=None,
        turn=1,
        log=log,
    )
    return state


def neighbor_positions(board: Dict[Tuple[int, int], PlacedTile]) -> List[Tuple[int, int]]:
    if not board:
        return [(0, 0)]
    positions = set()
    for x, y in board.keys():
        for dx, dy in DIRS.values():
            pos = (x + dx, y + dy)
            if pos not in board:
                positions.add(pos)
    return sorted(positions)


def can_place(board: Dict[Tuple[int, int], PlacedTile], tile: TileInstance, x: int, y: int) -> bool:
    if (x, y) in board:
        return False
    if not board:
        return True

    has_neighbor = False
    for side, (dx, dy) in DIRS.items():
        nx, ny = x + dx, y + dy
        neighbor = board.get((nx, ny))
        if neighbor is None:
            continue
        has_neighbor = True
        if neighbor.tile.edges[OPPOSITE[side]] != tile.edges[side]:
            return False
    return has_neighbor


def legal_positions(board: Dict[Tuple[int, int], PlacedTile], tile: TileInstance) -> List[Tuple[int, int]]:
    return [pos for pos in neighbor_positions(board) if can_place(board, tile, pos[0], pos[1])]


def all_legal_moves(board: Dict[Tuple[int, int], PlacedTile], template: TileTemplate) -> Dict[int, List[Tuple[int, int]]]:
    return {rotation: legal_positions(board, instantiate_tile(template, rotation)) for rotation in range(4)}


def region_label(region: RegionInstance) -> str:
    parts = [p for p in region.parts if p in DIRS]
    if region.feature == "monastery":
        return "修道院"
    if not parts:
        return FEATURE_LABELS.get(region.feature, region.feature)
    arrows = {"N": "北", "E": "東", "S": "南", "W": "西"}
    return f'{FEATURE_LABELS.get(region.feature, region.feature)} ({"/".join(arrows[p] for p in parts)})'


def walk_feature(board: Dict[Tuple[int, int], PlacedTile], start_coord: Tuple[int, int], start_region_id: str) -> Dict[str, object]:
    start_tile = board[start_coord]
    start_region = start_tile.tile.regions[start_region_id]
    feature = start_region.feature
    if feature not in {"road", "city"}:
        raise ValueError("walk_feature can only be used for road/city regions")

    stack: List[Tuple[Tuple[int, int], str]] = [(start_coord, start_region_id)]
    seen: set[Tuple[Tuple[int, int], str]] = set()
    open_edges = 0
    tiles = set()
    meeples: List[Tuple[Tuple[int, int], str, int]] = []

    while stack:
        coord, region_id = stack.pop()
        if (coord, region_id) in seen:
            continue
        seen.add((coord, region_id))
        placed = board[coord]
        region = placed.tile.regions[region_id]
        tiles.add(coord)

        if region_id in placed.meeples:
            meeples.append((coord, region_id, placed.meeples[region_id]))

        for part in region.parts:
            if part not in DIRS:
                continue
            dx, dy = DIRS[part]
            neighbor_coord = (coord[0] + dx, coord[1] + dy)
            neighbor = board.get(neighbor_coord)
            if neighbor is None:
                open_edges += 1
                continue
            neighbor_region_id = neighbor.edge_to_region.get(OPPOSITE[part])
            if neighbor_region_id is None:
                open_edges += 1
                continue
            neighbor_region = neighbor.tile.regions[neighbor_region_id]
            if neighbor_region.feature != feature:
                open_edges += 1
                continue
            stack.append((neighbor_coord, neighbor_region_id))

    return {
        "feature": feature,
        "regions": seen,
        "open_edges": open_edges,
        "complete": open_edges == 0,
        "tiles": tiles,
        "tile_count": len(tiles),
        "meeples": meeples,
    }


def count_surrounding_tiles(board: Dict[Tuple[int, int], PlacedTile], x: int, y: int) -> int:
    count = 0
    for nx in range(x - 1, x + 2):
        for ny in range(y - 1, y + 2):
            if (nx, ny) in board:
                count += 1
    return count


def can_place_meeple(
    board: Dict[Tuple[int, int], PlacedTile],
    tile: TileInstance,
    x: int,
    y: int,
    region_id: str,
) -> bool:
    region = tile.regions[region_id]
    if region.feature not in {"road", "city", "monastery"}:
        return False

    hypothetical = dict(board)
    hypothetical[(x, y)] = PlacedTile(tile=tile, x=x, y=y)

    if region.feature == "monastery":
        return True

    feature = walk_feature(hypothetical, (x, y), region_id)
    return len(feature["meeples"]) == 0


def get_available_meeple_regions(
    board: Dict[Tuple[int, int], PlacedTile],
    tile: TileInstance,
    x: int,
    y: int,
) -> List[str]:
    options = []
    for region_id, region in tile.regions.items():
        if region.feature in {"road", "city", "monastery"} and can_place_meeple(board, tile, x, y, region_id):
            options.append(region_id)
    return options


def add_score(state: GameState, player_index: int, points: int, reason: str) -> None:
    state.players[player_index].score += points
    state.log.append(f'{state.players[player_index].name} が {points} 点獲得: {reason}')


def score_completed_features(state: GameState, placed_coord: Tuple[int, int]) -> None:
    checked = set()
    placed = state.board[placed_coord]

    for region_id, region in placed.tile.regions.items():
        if region.feature not in {"road", "city"}:
            continue
        if (placed_coord, region_id) in checked:
            continue
        feature = walk_feature(state.board, placed_coord, region_id)
        checked.update(feature["regions"])
        if not feature["complete"] or not feature["meeples"]:
            continue

        points = feature["tile_count"] if feature["feature"] == "road" else feature["tile_count"] * 2
        counts: Dict[int, int] = {}
        for _, _, player_index in feature["meeples"]:
            counts[player_index] = counts.get(player_index, 0) + 1
        max_count = max(counts.values())
        winners = [player_index for player_index, count in counts.items() if count == max_count]

        feature_name = "道" if feature["feature"] == "road" else "都市"
        for player_index in winners:
            add_score(state, player_index, points, f'完成した{feature_name}')

        for coord, rid, player_index in feature["meeples"]:
            placed_tile = state.board[coord]
            del placed_tile.meeples[rid]
            state.players[player_index].meeples_available += 1

    score_completed_monasteries(state, placed_coord)


def score_completed_monasteries(state: GameState, placed_coord: Tuple[int, int]) -> None:
    px, py = placed_coord
    for x in range(px - 1, px + 2):
        for y in range(py - 1, py + 2):
            placed = state.board.get((x, y))
            if placed is None:
                continue
            for region_id, region in placed.tile.regions.items():
                if region.feature != "monastery":
                    continue
                if region_id not in placed.meeples:
                    continue
                if count_surrounding_tiles(state.board, x, y) == 9:
                    player_index = placed.meeples[region_id]
                    add_score(state, player_index, 9, "完成した修道院")
                    del placed.meeples[region_id]
                    state.players[player_index].meeples_available += 1


def draw_next_tile(state: GameState) -> bool:
    if state.current_tile is not None:
        return True

    while state.deck:
        template = state.deck.pop()
        moves = all_legal_moves(state.board, template)
        if any(moves[rotation] for rotation in range(4)):
            state.current_tile = template
            state.log.append(
                f'ターン {state.turn}: {state.active_player().name} が "{template.name}" を引きました。'
            )
            return True
        state.discarded_tiles.append(template.name)
        state.log.append(f'"{template.name}" は置ける場所がないため捨て札になりました。')

    state.current_tile = None
    finalize_game(state)
    return False


def place_current_tile(
    state: GameState,
    x: int,
    y: int,
    rotation: int,
    meeple_region_id: Optional[str] = None,
) -> None:
    if state.current_tile is None:
        raise ValueError("先にタイルを引いてください。")

    template = state.current_tile
    tile = instantiate_tile(template, rotation)

    if not can_place(state.board, tile, x, y):
        raise ValueError("その場所には配置できません。")

    placed = PlacedTile(tile=tile, x=x, y=y)
    state.board[(x, y)] = placed

    if meeple_region_id:
        if state.active_player().meeples_available <= 0:
            raise ValueError("このプレイヤーのミープルは残っていません。")
        if meeple_region_id not in tile.regions:
            raise ValueError("不正なミープル配置です。")
        if not can_place_meeple({k: v for k, v in state.board.items() if k != (x, y)}, tile, x, y, meeple_region_id):
            raise ValueError("その地形にはミープルを置けません。")
        placed.meeples[meeple_region_id] = state.current_player
        state.active_player().meeples_available -= 1
        state.log.append(
            f'{state.active_player().name} が ({x}, {y}) の {region_label(tile.regions[meeple_region_id])} にミープルを配置しました。'
        )

    state.log.append(
        f'{state.active_player().name} が "{template.name}" を ({x}, {y}) に {rotation * 90}° 回転で配置しました。'
    )
    state.current_tile = None

    score_completed_features(state, (x, y))

    state.current_player = (state.current_player + 1) % len(state.players)
    state.turn += 1

    if not state.deck:
        finalize_game(state)


def finalize_game(state: GameState) -> None:
    if state.final_scored:
        return

    scored_features = set()

    for coord, placed in list(state.board.items()):
        for region_id, player_index in list(placed.meeples.items()):
            region = placed.tile.regions[region_id]
            if region.feature in {"road", "city"}:
                if (coord, region_id) in scored_features:
                    continue
                feature = walk_feature(state.board, coord, region_id)
                scored_features.update(feature["regions"])

                counts: Dict[int, int] = {}
                for _, _, p_index in feature["meeples"]:
                    counts[p_index] = counts.get(p_index, 0) + 1
                if not counts:
                    continue
                max_count = max(counts.values())
                winners = [p_index for p_index, count in counts.items() if count == max_count]
                if region.feature == "road":
                    points = feature["tile_count"]
                    reason = "未完成の道"
                else:
                    points = feature["tile_count"]
                    reason = "未完成の都市"
                for winner in winners:
                    add_score(state, winner, points, reason)
                for coord2, rid2, p_index in feature["meeples"]:
                    if rid2 in state.board[coord2].meeples:
                        del state.board[coord2].meeples[rid2]
                        state.players[p_index].meeples_available += 1

            elif region.feature == "monastery":
                points = count_surrounding_tiles(state.board, coord[0], coord[1])
                add_score(state, player_index, points, "未完成の修道院")
                del placed.meeples[region_id]
                state.players[player_index].meeples_available += 1

    max_score = max(player.score for player in state.players)
    winners = [player.name for player in state.players if player.score == max_score]
    if len(winners) == 1:
        state.winner_text = f"勝者: {winners[0]} ({max_score} 点)"
    else:
        state.winner_text = f'引き分け: {", ".join(winners)} ({max_score} 点)'
    state.final_scored = True
    state.log.append("ゲーム終了。最終得点を計算しました。")


def get_board_bounds(board: Dict[Tuple[int, int], PlacedTile], padding: int = 1) -> Tuple[int, int, int, int]:
    xs = [x for x, _ in board.keys()]
    ys = [y for _, y in board.keys()]
    return min(xs) - padding, max(xs) + padding, min(ys) - padding, max(ys) + padding


def player_color(player_index: int) -> str:
    palette = ["#e74c3c", "#3498db", "#f39c12", "#9b59b6"]
    return palette[player_index % len(palette)]
