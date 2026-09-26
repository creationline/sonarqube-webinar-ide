"""
user_search.py

【6】SQL インジェクション
     ルール: python:S3649
            (Database queries should not be vulnerable to injection attacks)
     → push して SonarQube Cloud で解析すると検知される

外部から来た値を、文字列連結でそのまま SQL 文に埋め込んでいます。
教科書どおりの SQL インジェクションですが、IDE には指摘が出ません。

判定に必要なのは「その 1 行の書き方」ではなく、「値がどこから来て、
どこへ届くか」を追跡する汚染解析（Taint Analysis）だからです。

  source（危険な値の出発点）: request.args.get("keyword")
  sink  （到達点）          : cursor.execute()

今日はデモなので source と sink が隣に並んでいますが、実際の
プロジェクトではファイルも層もまたいで何段も関数を経由します。
プロジェクト全体を横断して全経路を追う解析はキーストロークごとに
走らせるものではないため、サーバー側（SonarQube Cloud）が担当します。

このファイルにはテストが 1 件もありません。ダッシュボードでは
カバレッジ 0% として表示されます（脆弱性があるファイルに限って
テストが無い、というのはよくある話です）。
"""

import sqlite3

from flask import Flask, request
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
# CSRF 保護を有効にする（python:S4502 対策。今日の仕込みとは無関係）
CSRFProtect(app)


# methods を明示する（python:S6965 対策。今日の仕込みとは無関係）
@app.route("/users/search", methods=["GET"])
def search_users() -> str:
    """キーワードでユーザーを検索する"""
    keyword = request.args.get("keyword", "")

    with sqlite3.connect("demo.db") as conn:
        cursor = conn.cursor()
        # 外部入力を文字列連結で SQL に埋め込んでいるのが問題のポイント
        # cursor.execute("SELECT id, name FROM users WHERE name LIKE '%" + keyword + "%'")
        # 外部入力はプレースホルダ（?）で渡し、SQL 文に直接埋め込まない
        cursor.execute("SELECT id, name FROM users WHERE name LIKE ?", ("%" + keyword + "%",))        
        rows = cursor.fetchall()

    return str(rows)
