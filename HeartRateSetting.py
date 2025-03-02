import requests
import gspread
from datetime import datetime
import pandas as pd
from gspread_dataframe import get_as_dataframe
import pytz
import json


#時間紀錄
def time_label(worksheet):
    """
    存入時間戳，並在每日 12:00:00 時分析數據
    """
    tz = pytz.timezone("Asia/Taipei")
    now_time = datetime.now(tz).strftime("%H:%M:%S")  # 只取時間部分
    full_now_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")  # 完整時間戳
    date = datetime.now(tz).strftime("%Y-%m-%d")
    #測試用時間戳
    #now_time = "12:00:00"
    column_name = 'time'
    header = worksheet.row_values(1)
    
    if column_name in header:
        col_index = header.index(column_name) + 1  
        column_values = worksheet.col_values(col_index)  
        next_row = len(column_values) + 1  

        # 存入當前時間
        worksheet.update_cell(next_row, col_index, full_now_time)
        print(f"成功將數據追加到 '{column_name}' 欄位，值為：{full_now_time}")
        print(f"目前監測時間戳為{now_time}")
    # 若時間為 12:00:00，則開始分析數據
    if now_time == "12:00:00":
        print("開始數據分析...")

        # 讀取 Google Sheet 數據為 DataFrame
        df = get_as_dataframe(worksheet, evaluate_formulas=True).dropna(how="all")  # 清理空白行
        if not {"heart-rate", "blood-oxygen", "time"}.issubset(df.columns):
            print("表格缺少必要欄位，請檢查 Google Sheet。")
            return
        # 篩選符合條件的資料暨資料清洗
        df.replace("NA", pd.NA, inplace=True)
        df["time"] = pd.to_datetime(df["time"], errors="coerce")
        df = df[df["time"].dt.strftime("%Y-%m-%d") == date]
        df["heart-rate"] = pd.to_numeric(df["heart-rate"], errors="coerce")
        df["blood-oxygen"] = pd.to_numeric(df["blood-oxygen"], errors="coerce")
        
        abnormal_heart_rate = df[(df["heart-rate"] > 120) | (df["heart-rate"] < 60) | (df["heart-rate"].isna())]
        abnormal_blood_oxygen = df[(df["blood-oxygen"] < 85) | (df["blood-oxygen"].isna())]

        # **合併異常資料**
        abnormal_data = pd.concat([abnormal_heart_rate, abnormal_blood_oxygen]).drop_duplicates()
        abnormal_data["time"] = abnormal_data["time"].astype(str)

        # **轉換為 JSON**
        result_json = abnormal_data.to_dict(orient="records")
        json_output = json.dumps(result_json, ensure_ascii=False, indent=2)

        print("異常數據 JSON：")
        print(json_output)

        return json_output
    
#google sheet設定
def setup_google_sheet():
    """
    設定 Google Sheet 並返回 worksheet 對象
    :param credentials_file: Google API 憑證檔案路徑
    :param sheet_url: Google Sheet 網址
    :param worksheet_index: 要操作的工作表索引（預設為第一個工作表）
    :return: worksheet 對象
    """
    credentials_file = 'heart-rate-token.json'
    sheet_url = "https://docs.google.com/spreadsheets/d/1QIhbqeoSqV1DE7FwmkWYqAYrFT-vh9B5bfh6lXosdMo/edit?usp=sharing"
    worksheet_index=0
    
    gc = gspread.service_account(filename=credentials_file)
    sheet = gc.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(worksheet_index)
    return worksheet

#血氧設定
def update_blood_oxygen_value(worksheet):
    """
    獲取血氧數值並寫入 Google Sheet
    :param api_url: API 網址
    :param headers: API 請求的 Header（包含 Authorization Token）
    :param worksheet: Google Sheet 的 worksheet 對象
    :param column_name: 要寫入的欄位名稱（如 "blood-oxygen"）
    """
    api_url = "https://e2live.duckdns.org:8155/api/states/sensor.spo2_2be1"
    headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI2Mjk0NmMzNjI2Nzc0YzJkOTkxZWFjYjk1NjkxZjgzZCIsImlhdCI6MTcxODc2Mzg5NywiZXhwIjoyMDM0MTIzODk3fQ.gq-oyg7bog6-1l8UW7QSiqTnQXzxrs0WbbE5qwIMaxI"
    }
    column_name = "blood-oxygen"
    # 發送 GET 請求
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        state_value = data.get("state")  # 取得 'state' 的值
        # if not isinstance(state_value, int):
        #     state_value = "NA"
        #     print(f"找不到值{state_value}，用NA替代")
        # 在 Google Sheet 中尋找指定欄位名稱
        header = worksheet.row_values(1)  # 取得標題列
        if column_name in header:
            col_index = header.index(column_name) + 1  # 找到欄位索引（1-based）

            # 找到欄位目前的最後一行
            column_values = worksheet.col_values(col_index)  # 獲取該欄位所有值
            next_row = len(column_values) + 1  # 下一行的行號（空行）

            # 將數值寫入下一行
            worksheet.update_cell(next_row, col_index, state_value)
            print(f"成功將數據追加到 '{column_name}' 欄位，值為：{state_value}")
        else:
            print(f"找不到 '{column_name}' 欄位，請確認 Sheet 的標題列！")
    else:
        print(f"API 請求失敗，狀態碼：{response.status_code}")
        print(response.text)

#心率設定
def update_heart_rate_value(worksheet):
    """
    獲取心律數值並寫入 Google Sheet
    :param api_url: API 網址
    :param headers: API 請求的 Header（包含 Authorization Token）
    :param worksheet: Google Sheet 的 worksheet 對象
    :param column_name: 要寫入的欄位名稱（如 "blood-oxygen"）
    """
    api_url = "https://e2live.duckdns.org:8155/api/states/sensor.heart_rate_2be1"
    headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI2Mjk0NmMzNjI2Nzc0YzJkOTkxZWFjYjk1NjkxZjgzZCIsImlhdCI6MTcxODc2Mzg5NywiZXhwIjoyMDM0MTIzODk3fQ.gq-oyg7bog6-1l8UW7QSiqTnQXzxrs0WbbE5qwIMaxI"
    }
    column_name = 'heart-rate'
    # 發送 GET 請求
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        state_value = data.get("state")  # 取得 'state' 的值
        # if not isinstance(state_value, int):
        #     state_value = "NA"
        #     print(f"找不到值{state_value}，用NA替代")
        # 在 Google Sheet 中尋找指定欄位名稱
        header = worksheet.row_values(1)  # 取得標題列
        if column_name in header:
            col_index = header.index(column_name) + 1  # 找到欄位索引（1-based）

            # 找到欄位目前的最後一行
            column_values = worksheet.col_values(col_index)  # 獲取該欄位所有值
            next_row = len(column_values) + 1  # 下一行的行號（空行）

            # 將數值寫入下一行
            worksheet.update_cell(next_row, col_index, state_value)
            print(f"成功將數據追加到 '{column_name}' 欄位，值為：{state_value}")
        else:
            print(f"找不到 '{column_name}' 欄位，請確認 Sheet 的標題列！")
    else:
        print(f"API 請求失敗，狀態碼：{response.status_code}")
        print(response.text)