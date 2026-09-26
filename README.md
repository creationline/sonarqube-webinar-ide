# SonarQube Webinar IDE Demo

SonarQube for IDE と SonarQube Cloud のデモ用リポジトリです。
**わざと問題のあるコードを入れています。本番環境では使わないでください。**

## このデモで見せること

- **手元（IDE）**：コードを書いたその場で問題を検知する
- **サーバー（SonarQube Cloud）**：プロジェクト全体を横断する解析（SQL インジェクションの汚染解析）、カバレッジ、SBOM
- **Quality Gate**：SQL インジェクションを含む Pull Request をマージできないようにする

## ファイル構成

| ファイル | 内容 |
|---|---|
| `user_manager.py` | IDE で検知される問題（2 件） |
| `test_user_manager.py` | テストコードの問題（3 件）。テストは意図的に半分だけ書いてある |
| `user_search.py` | SQL インジェクション（サーバー側でのみ検知） |
| `sonar-project.properties` | SonarQube Cloud の解析設定 |
| `.github/workflows/sonar.yml` | テスト、カバレッジ計測、SonarQube Cloud スキャンを実行する CI |

## 仕込んである問題

| # | 内容 | ルール | 検知される場所 |
|---|---|---|---|
| 3 | ZIP を無制限に展開（Zip Bomb） | python:S5042 | IDE |
| 4 | 制御構文のネストが深すぎる | python:S134 | IDE |
| 5 | いつも成功してしまう assert | python:S5905 | IDE |
| 5-2 | 例外ブロックの後ろに書いた assert | python:S5915 | IDE |
| 5-3 | 名前のせいで実行されないテスト | python:S5899 | IDE |
| 6 | SQL インジェクション | python:S3649 | SonarQube Cloud のみ |

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

VS Code では次の 2 つを行います。

1. インタープリターに `./.venv/bin/python` を選ぶ
2. SonarQube for IDE 拡張機能を入れて、Connected Mode で SonarQube Cloud に接続する

## テストとカバレッジ

```bash
# テストを実行
python3 -m unittest test_user_manager -v

# カバレッジを計測（CI と同じコマンド）
coverage run --source=. --omit="test_*.py" -m unittest discover
coverage xml
```

## SonarQube Cloud / GitHub の設定

- **解析方法**：CI-based analysis を使い、Automatic Analysis は無効にする（有効なままだとカバレッジが取り込めない）
- **トークン**：GitHub の Secrets に `SONAR_TOKEN` を登録する
- **Quality Gate**：条件を「Security Rating on New Code is worse than A」の 1 つだけにしたものを割り当てる
- **ブランチ保護**：main で SonarQube Cloud のチェックを必須にし、管理者のバイパスも禁止する

## デモの流れ（概要）

1. `user_search.py` を含まない状態の main で、IDE の検知を見せる
2. `user_search.py` を開き、IDE では SQL インジェクションが検知されないことを見せる
3. ブランチを切って `user_search.py` を追加し、Pull Request を作る
4. Quality Gate が Failed になり、マージできないことを見せる
5. SonarQube Cloud で、SQL インジェクションの経路、カバレッジ、SBOM を見せる
