"""
test_user_manager.py

user_manager.py のテストコードです。ここには仕掛けが 4 つあります。
テーマは「PASS するのに、実は何も守っていないテスト」です。

  【5】  いつも成功してしまう assert（python:S5905）
         → assert が「必ず成功する」
  【5-2】例外ブロックの後ろに書いた assert（python:S5915）
         → assert が「一度も実行されない」
  【5-3】名前のせいで実行されないテスト（python:S5899）
         → テストそのものが「一度も実行されない」
         ※ 3 つとも、書いているその場で IDE が検知する

  ★ テストを「半分だけ」書いている
       → push 後、SonarQube Cloud のダッシュボードで
         カバレッジ 約 50% として表示される。
         どの行にテストが通っていないかも行単位で分かる。

  実行:
    python3 -m unittest test_user_manager -v

  カバレッジ計測（CI と同じコマンド）:
    coverage run --source=. --omit="test_*.py" -m unittest discover
    coverage xml
"""

import unittest

from user_manager import import_archive, user_rank


class TestUserRank(unittest.TestCase):
    """user_rank() の判定ロジックを確認する"""

    # ============================================================
    # 【5】いつも成功してしまう assert
    #     ルール: python:S5905
    #            (Assert should not be called on a tuple literal)
    # ============================================================
    #
    # ■ 何が起きているのか
    #
    # よくある誤解は「テストが実行されなくなる」ですが、そうではありません。
    # テストはちゃんと実行されます。assert の行も実行されます。
    # 壊れているのは「何を検査しているか」のほうです。
    #
    # assert は関数ではないので、括弧を付けても引数を囲んだことになりません。
    # 括弧はタプルを作ります。1 行ずつ追うとこうなります。
    #
    #   assert (result["rank"] == "S", "管理者で高得点なら S になるはず")
    #
    #     ① 括弧の中身は評価される
    #        → result["rank"] == "S" は計算され、True か False になる
    #
    #     ② その結果を第 1 要素にしたタプルが組み立てられる
    #        → (False, "管理者で高得点なら S になるはず")
    #
    #     ③ assert が真偽を見るのは、この「タプルそのもの」
    #        → 空でないタプルは常に真
    #        → assert は絶対に失敗しない
    #
    # ①の比較結果は、②で袋に詰められた時点で誰にも見られなくなります。
    # 計算はされているのに、捨てられているわけです。
    #
    # ■ なぜ厄介なのか
    #
    # スキップされたテストなら、レポートに「skipped」と出るので気づけます。
    # これは違います。堂々と PASS します。緑になります。
    # 「テストは全部通っています」という報告まで、何も嘘はついていません。
    # ただ、そのうち 1 件は何も守っていないだけです。
    #
    # user_rank() の中身を壊してみると、はっきりします。
    # たとえば rank = "S" を rank = "Z" に書き換えても、
    # このテストは落ちません。バグを通してしまいます。
    #
    # Python 自身もコンパイル時に
    #   SyntaxWarning: assertion is always true, perhaps remove parentheses?
    # という警告を出しますが、テストは PASS のままなので、
    # CI のログに流れて誰も見ない、という形で見逃されます。
    # SonarQube for IDE は、これを書いているその場で赤い波線にします。
    #
    # ■ どう直すか
    #
    #   (1) 括弧を 2 文字消す —— これで assert は本来の形に戻る
    #
    #         assert (result["rank"] == "S", "…")   ← いつも成功する
    #         assert result["rank"] == "S", "…"     ← ちゃんと失敗する
    #
    #   (2) unittest を使っているなら self.assertEqual() に書き換える
    #       （下の test_non_admin_is_rank_c がこの形です）
    #
    #         self.assertEqual(result["rank"], "S", "…")
    #
    #       こちらはそもそも関数なので、括弧を付けても壊れません。
    #       失敗したときに「S を期待したが Z だった」と差分も出ます。
    #
    #   (3) 直したあと、一度わざとテストを失敗させて確かめる
    #
    #       期待値を "S" から "Z" に変えて実行し、赤くなることを見ます。
    #       落ちなければ、そのテストはまだ何も守っていません。

    def test_admin_with_high_score_is_rank_s(self):
        """管理者・18 歳以上・JP・80 点以上なら S ランク"""
        result = user_rank({"role": "admin", "age": "30", "country": "JP", "score": "90"})

        # ↓ 括弧を付けているせいでタプルを assert している。ここが問題のポイント
        assert (result["rank"] == "S", "管理者で高得点なら S になるはず")

    def test_non_admin_is_rank_c(self):
        """管理者以外は C ランク（こちらは正しい書き方）"""
        result = user_rank({"role": "member", "age": "30", "country": "JP", "score": "90"})

        # ↓ unittest の assertEqual を使っている。失敗すれば必ず落ちる
        self.assertEqual(result["rank"], "C")

    def test_minor_is_out_of_scope(self):
        """18 歳未満は対象外（こちらも正しい書き方）"""
        result = user_rank({"role": "admin", "age": "15", "country": "JP", "score": "90"})

        self.assertEqual(result["rank"], "対象外（未成年）")

    # ============================================================
    # 【5-2】例外ブロックの後ろに書いた assert
    #     ルール: python:S5915
    #            (Assertions should not be made at the end of blocks
    #             expecting an exception)
    # ============================================================
    #
    # ■ 何が起きているのか
    #
    # with self.assertRaises(...) の中で例外が出ると、その瞬間に
    # with ブロックを抜けます。例外を出した行より後ろは実行されません。
    #
    #   with self.assertRaises(FileNotFoundError):
    #       result = import_archive("no_such_file.zip")   ← ここで例外
    #       self.assertEqual(result["status"], "error")   ← 一度も実行されない
    #
    # 「例外が出ること」と「そのあとの戻り値」の両方を確認したつもりでも、
    # 実際に確認しているのは前者だけです。
    # しかも後ろの assert は中身が間違っていても（"error" は返りません）、
    # 実行されないので誰にも気づかれません。テストは PASS します。
    #
    # ■ どう直すか
    #
    #   例外を出す行を with ブロックの最後の 1 行にする。
    #   戻り値を確認したいなら、例外が出ないケースとして別のテストに分ける。
    #
    #     with self.assertRaises(FileNotFoundError):
    #         import_archive("no_such_file.zip")

    def test_missing_archive_raises(self):
        """存在しない ZIP を渡したら FileNotFoundError になる"""
        with self.assertRaises(FileNotFoundError):
            result = import_archive("no_such_file.zip")
            # ↓ 上の行で例外が出た瞬間に with を抜けるので、ここは一度も実行されない
            self.assertEqual(result["status"], "error")

    # ============================================================
    # 【5-3】名前のせいで実行されないテスト
    #     ルール: python:S5899 (Test methods should be discoverable)
    # ============================================================
    #
    # ■ 何が起きているのか
    #
    # unittest が自動で実行するのは、名前が "test" で始まるメソッドだけです。
    # 下のメソッドは check_ で始まっているので、テストとして認識されません。
    #
    # 中身は正しく書けています。assertEqual も使っています。
    # それでも、一度も実行されていません。
    #
    # ■ なぜ厄介なのか
    #
    # 【5】と同じく、レポートに「skipped」とも「failed」とも出ません。
    # 実行件数が 1 件少ないだけです。4 件書いたつもりが 3 件しか走っていない
    # ことに、件数を数えない限り気づけません。
    #
    # push 後のカバレッジでは、このテストが確認するはずだった
    # rank = "B" の行が「未テスト（赤）」のまま残ります。
    # 「テストは書いてあるのに、なぜか赤い」という形で表に出てきます。
    #
    # ■ どう直すか
    #
    #   メソッド名の先頭を test_ にする。それだけです。
    #
    #     def check_foreign_admin_is_rank_b(self):   ← 実行されない
    #     def test_foreign_admin_is_rank_b(self):    ← 実行される

    def check_foreign_admin_is_rank_b(self):
        """JP 以外の管理者は B ランク"""
        result = user_rank({"role": "admin", "age": "30", "country": "US", "score": "90"})

        # ↓ 中身は正しい。名前が test_ で始まっていないことだけが問題
        self.assertEqual(result["rank"], "B")


if __name__ == "__main__":
    unittest.main()


# ============================================================
# メモ：ここから下は「わざと書いていないテスト」の一覧
# ------------------------------------------------------------
# カバレッジのデモのために、テストは意図的に半分で止めてあります。
# push 後、ダッシュボードの Measures > Coverage から
# user_manager.py を開くと、次の行が「未テスト（赤）」で並びます。
#
#   ・import_archive()   … 正常に展開できたケースのテストが無い
#                           （ファイルが無いときの例外テストだけ）
#   ・rank = "A"         … 80 点未満の分岐
#   ・rank = "B"         … JP 以外の分岐。テスト（【5-3】）は書いてあるのに
#                           名前のせいで実行されないので赤いまま
#   ・except ValueError: … 数値が不正だったときのエラー処理
#   ・user_search.py     … ファイルまるごと（カバレッジ 0%）
#
# 注目してほしいのは最後の except です。
# 「正常系だけテストを書いて、異常系は誰も通していない」という、
# 実プロジェクトで最も多いパターンがそのまま出ています。
# 行単位で赤くなるので、次にどのテストを書くべきかが一目で決まります。
#
# ============================================================
# メモ：カバレッジの計測について
# ------------------------------------------------------------
# sonar-project.properties に
#
#   sonar.tests=test_user_manager.py
#
# を宣言してあります。テストコード自身がカバレッジの母数に
# 入ってしまうのを防ぐための設定です。
# ============================================================
