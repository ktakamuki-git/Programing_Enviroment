import os
import csv
import time
import google.generativeai as genai
from PIL import Image
import pdf2image

# --- 設定項目 ---
API_KEY = "YOUR_GEMINI_API_KEY"  # ここにご自身のAPIキーを入力してください
MODEL_NAME = "gemini-1.5-flash"
INPUT_PDF = "amex_statement.pdf"
OUTPUT_CSV = "amex_parsed.csv"

# Gemini APIの初期化
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

def convert_pdf_to_images(pdf_path):
    """PDFを画像リストに変換する"""
    print(f"[*] PDFを読み込み中: {pdf_path}")
    # 300dpi程度で読み込むとOCR精度が安定します
    return pdf2image.convert_from_path(pdf_path, dpi=300)

def analyze_page(image, page_num):
    """1ページごとにGemini APIで解析し、CSV行のリストを返す"""
    prompt = f"""
    これはAmerican Expressの利用明細書（スキャンデータ）の{page_num}ページ目です。
    記載されているすべての「カード利用明細」を抽出してください。
    
    出力は以下のCSVフォーマットのみを返してください。解説やヘッダーは不要です。
    
    【フォーマット】
    日付(YYYYMMDD),キーワード,入金,出金,摘要
    
    【抽出・変換ルール】
    1. 日付: 明細上の「月/日」を YYYYMMDD 形式に変換。年はこの明細書の発行年から判断してください。
    2. キーワード: 常に空文字 "" としてください。
    3. 入金: 振込、返金、マイナス表記など、口座へのプラス要素があればその金額。なければ 0。
    4. 出金: カード利用金額。
    5. 摘要: 利用店名、場所などの内容をそのまま抽出。
    
    ※明細行がないページ（表紙や広告など）の場合は「NO_DATA」とだけ出力してください。
    ※Markdownのコードブロック(```)は使用せず、テキストのみ返してください。
    """
    
    print(f"[*] {page_num}ページ目を解析中...")
    response = model.generate_content([prompt, image])
    return response.text.strip()

def main():
    try:
        # 1. PDFを画像に変換
        images = convert_pdf_to_images(INPUT_PDF)
        
        final_csv_data = []
        # ヘッダーの追加
        final_csv_data.append(["日付(YYYYMMDD)", "キーワード", "入金", "出金", "摘要"])
        
        # 2. ページごとにループ処理
        for i, img in enumerate(images):
            raw_text = analyze_page(img, i + 1)
            
            if "NO_DATA" in raw_text:
                continue
                
            # 各行をパースしてリストに追加
            lines = raw_text.split('\n')
            for line in lines:
                if ',' in line:
                    # 前後の不要な空白やクォーテーションを削除
                    items = [item.strip().replace('"', '') for item in line.split(',')]
                    if len(items) >= 5:
                        final_csv_data.append(items[:5])
            
            # レートリミット回避のための待機（無料枠利用を想定）
            time.sleep(3)
            
        # 3. CSVファイルへ保存
        with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(final_csv_data)
            
        print(f"\n[完了] '{OUTPUT_CSV}' に保存しました。全{len(final_csv_data)-1}件の明細が見つかりました。")
        
    except Exception as e:
        print(f"\n[エラー] {e}")

if __name__ == "__main__":
    main()