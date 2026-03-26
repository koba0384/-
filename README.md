# carcassonne-streamlit

Streamlit で動く **カルカソンヌ風タイル配置ゲーム** の最小実装です。  
GitHub にそのまま push して、Streamlit Community Cloud で公開しやすい構成にしてあります。

## 入っているもの

- 2〜4人プレイ
- タイルを引く
- 回転して合法配置
- 道 / 都市 / 修道院へのミープル配置
- 完成時の即時得点
- 山札終了時の最終集計
- 盤面の簡易ビジュアル表示

## この MVP の簡略化ポイント

- ベースゲーム風の自作タイルセットです
- 草地（農夫）得点は省略
- 特殊拡張ルールは未実装
- 都市の紋章ボーナスは未実装

## ローカル実行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## GitHub に置く

```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

## Streamlit Community Cloud で公開

1. GitHub にこのコードを push
2. Streamlit Community Cloud で GitHub を連携
3. リポジトリを選択
4. `app.py` を起動ファイルに指定
5. Deploy

## フォルダ構成

```text
carcassonne-streamlit/
├─ app.py
├─ requirements.txt
├─ README.md
├─ .streamlit/
│  └─ config.toml
└─ carcassonne_app/
   ├─ __init__.py
   ├─ core.py
   └─ render.py
```
