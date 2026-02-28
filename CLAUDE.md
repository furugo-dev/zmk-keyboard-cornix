# CLAUDE.md

## プロジェクト概要

Cornixスプリットキーボード用ZMKファームウェア設定リポジトリ。
薙刀式（Naginata）日本語入力とHome Row Mods（HRM）を採用した個人キーマップを含む。

## 重要ファイル

```
config/cornix.keymap   # メインのキーマップ設定
config/                # ZMK設定ファイル群（.conf, .dtsi等）
boards/jzf/cornix/     # ボード定義ファイル
Justfile               # ビルドコマンド定義
build.yaml             # ビルドターゲット定義
flake.nix              # Nix開発環境
firmware/              # ビルド成果物（.uf2）出力先
```

## ビルドコマンド

```bash
just list              # ビルドターゲット一覧
just build <expr>      # 特定ターゲットをビルド（例: just build cornix_left）
just build all         # 全ターゲットをビルド
just clean             # ビルドキャッシュと成果物を削除
just init              # west初期化（初回セットアップ）
just update            # west依存関係を更新
```

ビルドには `ZMK_LIB_PREFIX` 環境変数にZMKライブラリの親ディレクトリを設定する必要がある。

## レイヤー構成

| 番号 | 名前 | 用途 |
|------|------|------|
| 0 | BASE | デフォルト英字レイヤー |
| 1 | NAGI | 薙刀式日本語入力レイヤー |
| 2 | LOWER | 数字・記号レイヤー |
| 3 | RAISE | 括弧・矢印キーレイヤー |
| 4 | ADJUST | Functionキー・マウス操作（LOWER+RAISE同時押しで起動） |
| 5 | DEBUG | BT設定・bootloader |

## HRM（Home Row Mods）設計方針

### タイミング定数

```c
HM_TAPPING_TERM      250ms  // CTL/ALT/GUI用
HM_TAPPING_TERM_FAST 200ms  // Shift用
HM_PRIOR_IDLE         70ms  // 通常HRMのrequire-prior-idle
HM_PRIOR_IDLE_NG     250ms  // 薙刀式HRMのrequire-prior-idle
```

### ビヘイビア一覧

| ビヘイビア | flavor | 用途 |
|-----------|--------|------|
| `hm_l` / `hm_r` | tap-preferred | 左右のCTL/ALT/GUI HRM |
| `hm_shift_l` / `hm_shift_r` | balanced | 左右のShift HRM |
| `hm_ng_l` / `hm_ng_r` | tap-preferred | 薙刀式レイヤーのCTL/ALT/GUI HRM |
| `hm_ng_shift_l` / `hm_ng_shift_r` | balanced | 薙刀式レイヤーのShift HRM |

### 薙刀式HRMの特徴

- `hold-trigger-key-positions` から `KEYS_T`（親指キー）を除外 → 親指シフトとの干渉防止
- `require-prior-idle-ms=250` → コード入力中の誤tap/hold判定防止
- `hold-trigger-on-release` なし → 不要な遅延を排除
- hold時は `mod_nagi` マクロ経由でBASEレイヤーへ一時切替し、モディファイア送信後NAGIに復帰

## 薙刀式レイヤー操作

| 操作 | コンボ |
|------|--------|
| 薙刀式ON | H+J キー同時押し（key-positions 18+19） |
| 薙刀式OFF | F+G キー同時押し（key-positions 16+17） |
| ESC + 英字モード | W+R キー同時押し（key-positions 2+4、BASE/NAGIレイヤー共通） |

## サブエージェント使用ガイドライン

コストパフォーマンスを優先するため、以下のモデル選択方針に従うこと。

| タスク例 | モデル |
|---------|--------|
| ファイル検索・コード探索・単純な調査 | `haiku` |
| キーマップの変更・計画立案・中程度の分析 | `sonnet`（デフォルト） |
| 複雑なアーキテクチャ設計・大規模リファクタリング | `opus` |

- Explore エージェント（コードベース探索）は常に `haiku` を使用する
- 検索結果を確認するだけのリサーチは `haiku` で十分
- コード生成・編集を伴う場合のみ `sonnet` 以上を使用する

## フラッシュ手順

1. キーボードをUF2ブートローダーモードに（リセットボタンをダブルタップ）
2. `firmware/cornix_left.uf2` を左半分にドラッグ＆ドロップ
3. `firmware/cornix_right.uf2` を右半分にドラッグ＆ドロップ
4. 両半分を同時にリセット

> v2.3以降はSoftDevice復元不要。直接フラッシュ可能。