"""SonarQube for IDE のデモ用サンプル（わざと問題を入れています）。"""

import zipfile

# ============================================================
# 【3】ZIP を無制限に展開している（Zip Bomb）
#     ルール: python:S5042
#            (Expanding archive files should not be done without
#             controlling resource consumption)
# ------------------------------------------------------------
# extractall() は、展開後のサイズを一切確認せずに全部書き出します。
# 数十 KB の ZIP が展開すると数十 GB になる、という細工が可能で、
# ディスクを埋め尽くしてサービスを停止させられます（Zip Bomb）。
#
# 正しくは ZipInfo.file_size を先に合計し、
# 上限を超えるものは展開せずに弾きます。
# ============================================================
UPLOAD_DIR = "/var/app/uploads"


def import_archive(archive_path: str) -> dict[str, str]:
    """アップロードされた ZIP を展開して取り込む"""
    # ↓ 展開後のサイズを確認せずに丸ごと展開しているのが危険なポイント
    zipfile.ZipFile(archive_path).extractall(UPLOAD_DIR)

    return {"status": "imported"}


# ============================================================
# 【4】制御構文のネストが深すぎる
#     ルール: python:S134
#            (Control flow statements "if", "for", "while", "try"
#             and "with" should not be nested too deeply)
# ------------------------------------------------------------
# try の中に if、その中にまた if…と 5 段まで潜っています。
# 既定の上限は 4 段なので、5 段目で指摘が出ます。
#
# 動きはしますが、条件を 1 つ足すたびに読み手の負担が跳ね上がり、
# 修正時にバグを埋め込みやすい形です。
#
# 正しくは「早期リターン（ガード節）」で、
# 条件に合わないものを先に return して段数を減らします。
# ============================================================
def user_rank(params: dict[str, str]) -> dict[str, str]:
    """ユーザーのランクを判定する"""
    role = params.get("role", "")
    country = params.get("country", "")
    rank = "C"

    # ↓ ここから 5 段のネストが始まるのが問題のポイント
    try:
        age = int(params.get("age", "0"))
        score = int(params.get("score", "0"))

        if role == "admin":
            if age >= 18:
                if country == "JP":
                    if score >= 80:
                        rank = "S"
                    else:
                        rank = "A"
                else:
                    rank = "B"
            else:
                rank = "対象外（未成年）"
    except ValueError:
        rank = "不明（数値が不正）"

    return {"rank": rank}


if __name__ == "__main__":
    # 動作確認用（解析結果には影響しません）
    print(user_rank({"role": "admin", "age": "30", "country": "JP", "score": "90"}))
