
from __future__ import annotations

import streamlit as st

from carcassonne_app.core import (
    FEATURE_LABELS,
    GameState,
    all_legal_moves,
    draw_next_tile,
    get_available_meeple_regions,
    instantiate_tile,
    new_game,
    place_current_tile,
    region_label,
)
from carcassonne_app.render import render_board_html, render_tile_card_html


st.set_page_config(page_title="カルカソンヌ風 Streamlit", layout="wide")


def reset_game(num_players: int, seed_value: str) -> None:
    seed = int(seed_value) if seed_value.strip() else None
    st.session_state.game = new_game(num_players=num_players, seed=seed)
    st.session_state.rotation = 0
    st.session_state.position_choice = None
    st.session_state.meeple_choice = "置かない"
    st.session_state.flash = ""


def get_game() -> GameState:
    if "game" not in st.session_state:
        st.session_state.game = new_game(num_players=2)
    if "rotation" not in st.session_state:
        st.session_state.rotation = 0
    if "position_choice" not in st.session_state:
        st.session_state.position_choice = None
    if "meeple_choice" not in st.session_state:
        st.session_state.meeple_choice = "置かない"
    if "flash" not in st.session_state:
        st.session_state.flash = ""
    return st.session_state.game


def safe_rerun_with_message(message: str) -> None:
    st.session_state.flash = message
    st.rerun()


game = get_game()

st.title("カルカソンヌ風タイルゲーム")
st.caption("GitHub にそのまま置ける Streamlit 向け MVP。2〜4人、タイル配置・ミープル・得点・最終集計まで入り。")

with st.sidebar:
    st.header("ゲーム設定")
    players_for_reset = st.selectbox("プレイヤー数", [2, 3, 4], index=min(len(game.players), 4) - 2)
    seed_for_reset = st.text_input("乱数シード（任意）", value="")
    if st.button("新しいゲーム", use_container_width=True):
        reset_game(players_for_reset, seed_for_reset)

    st.divider()
    st.subheader("スコア")
    for idx, player in enumerate(game.players):
        leader = " ← 手番" if idx == game.current_player and not game.final_scored else ""
        st.markdown(
            f'**{player.name}**: {player.score} 点 / ミープル {player.meeples_available} 個{leader}'
        )

    st.divider()
    st.subheader("山札")
    st.write(f"残りタイル: {len(game.deck)}")
    st.write(f"捨て札: {len(game.discarded_tiles)}")

    with st.expander("この実装のルール", expanded=False):
        st.markdown(
            """
- 置ける場所がないタイルは自動で捨て札になります。
- 道・都市・修道院にミープルを置けます。
- 完成した道は **タイル枚数 = 得点**。
- 完成した都市は **タイル枚数 × 2 = 得点**。
- 完成した修道院は **9点**。
- 最終集計では未完成の道・都市・修道院も点になります。
- 農夫（草地）の得点はこの MVP では省略しています。
            """
        )

flash = st.session_state.flash
if flash:
    st.info(flash)
    st.session_state.flash = ""

if game.final_scored:
    st.success(game.winner_text)

top_col1, top_col2 = st.columns([2.4, 1.1], gap="large")

with top_col1:
    st.subheader("盤面")
    st.markdown(render_board_html(game.board), unsafe_allow_html=True)

with top_col2:
    st.subheader("現在のタイル")
    if game.current_tile is None and not game.final_scored:
        st.write(f"手番: {game.active_player().name}")
        if st.button("タイルを引く", use_container_width=True):
            drew = draw_next_tile(game)
            if drew:
                st.session_state.rotation = 0
                st.session_state.position_choice = None
                st.session_state.meeple_choice = "置かない"
                safe_rerun_with_message("タイルを引きました。")
            else:
                safe_rerun_with_message("山札が尽きたので最終集計しました。")
    elif game.current_tile is None and game.final_scored:
        st.write("ゲーム終了")
    else:
        rotation = st.select_slider(
            "回転",
            options=[0, 1, 2, 3],
            value=st.session_state.rotation,
            format_func=lambda value: f"{value * 90}°",
            key="rotation",
        )

        tile = instantiate_tile(game.current_tile, rotation)
        st.markdown(render_tile_card_html(tile), unsafe_allow_html=True)
        st.caption(game.current_tile.name)

        moves_by_rotation = all_legal_moves(game.board, game.current_tile)
        legal_for_rotation = moves_by_rotation[rotation]

        if not legal_for_rotation:
            st.warning("この回転では置ける場所がありません。")
        else:
            options = [f"({x}, {y})" for x, y in legal_for_rotation]
            pos_label = st.selectbox(
                "配置場所",
                options=options,
                key="position_choice",
            )
            selected_index = options.index(pos_label)
            x, y = legal_for_rotation[selected_index]

            available_region_ids = get_available_meeple_regions(game.board, tile, x, y)
            meeple_options = ["置かない"] + [
                f"{region_id}: {region_label(tile.regions[region_id])}" for region_id in available_region_ids
            ]
            st.selectbox("ミープル", options=meeple_options, key="meeple_choice")

            if st.button("ここに配置", type="primary", use_container_width=True):
                choice = st.session_state.meeple_choice
                meeple_region_id = None if choice == "置かない" else choice.split(":", 1)[0]
                try:
                    place_current_tile(game, x=x, y=y, rotation=rotation, meeple_region_id=meeple_region_id)
                except ValueError as exc:
                    safe_rerun_with_message(f"配置できませんでした: {exc}")
                else:
                    st.session_state.position_choice = None
                    st.session_state.meeple_choice = "置かない"
                    st.session_state.rotation = 0
                    if game.final_scored:
                        safe_rerun_with_message("配置しました。山札が尽きたので最終集計しました。")
                    else:
                        safe_rerun_with_message("配置しました。次のプレイヤーの手番です。")

score_col, info_col = st.columns([1.2, 1.8], gap="large")

with score_col:
    st.subheader("プレイヤー一覧")
    rows = []
    for idx, player in enumerate(game.players):
        turn_mark = "🟡" if idx == game.current_player and not game.final_scored else ""
        rows.append(
            {
                "プレイヤー": f"{turn_mark} {player.name}".strip(),
                "得点": player.score,
                "残りミープル": player.meeples_available,
            }
        )
    st.table(rows)

with info_col:
    with st.expander("プレイログ", expanded=True):
        for line in reversed(game.log[-20:]):
            st.write("•", line)
