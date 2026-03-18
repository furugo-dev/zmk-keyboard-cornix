ZMKファームウェアのビルド → キーマップ可視化 → コミット＆プッシュを一連で行う。

## 手順

### 1. ビルド

```bash
just docker-build all
```

失敗したら原因を報告して中断する。成功したら次へ進む。

### 2. キーマップ可視化

```bash
just docker-draw cornix
```

`docs/img/cornix-keymap.svg` を更新する。

### 3. 変更内容の確認

`git diff --stat` と `git status` で変更ファイルを確認する。
変更内容からブランチ名を自動生成する（例: `feat/update-keymap-20260319`, `fix/adjust-layer` など）。
ブランチ名をユーザーに提示して確認を取る。

### 4. コミット＆プッシュ

確認が取れたら以下を実行する:

1. `git checkout -b <branch-name>`（すでにブランチにいる場合はスキップ）
2. 変更ファイルをステージング（`config/*.keymap`, `docs/img/*.svg`, `Justfile` など関連ファイル）
3. `git commit` （変更内容を要約したメッセージ）
4. `git push -u origin <branch-name>`

完了後にブランチ名とプッシュ先URLを報告する。
