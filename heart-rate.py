import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict
from gspread_dataframe import get_as_dataframe
from langchain.tools import tool
import pandas as pd
import pytz
from openai import OpenAI
import os

url = os.getenv("URL")
import os

url = os.getenv("URL")
import os

url = os.getenv("URL")

def read_google_sheet_heart_rate()-> Dict:
    """讀取heart-rate在google sheet中的數值"""
    print("\n開始讀取 Heart-Rate數值")
    try:
        scopes  = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        creds = Credentials.from_service_account_file(
            'agents/智慧管家/secrets/heart-rate-token.json', 
            scopes=scopes
        )
        client = gspread.authorize(creds)
        sheet_url = url
        sheet = client.open_by_url(sheet_url).get_worksheet(0)
        return sheet
    except Exception as e:
        print(f"讀取 Google Sheet 時發生錯誤: {str(e)}")
        raise

def Read_info(sheet):
    print("開始數據分析...")
    worksheet = sheet
    tz = pytz.timezone("Asia/Taipei")
    date = datetime.now(tz).strftime("%Y-%m-%d")
    
    # 讀取 Google Sheet 數據為 DataFrame
    df = get_as_dataframe(worksheet, evaluate_formulas=True).dropna(how="all")  # 清理空白行
    if not {"heart-rate", "blood-oxygen", "time"}.issubset(df.columns):
        print("表格缺少必要欄位，請檢查 Google Sheet。")
        return
    # 資料清洗
    df.replace("NA", pd.NA, inplace=True)
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df[df["time"].dt.strftime("%Y-%m-%d") == date] #只對當天資料做處理
    df["heart-rate"] = pd.to_numeric(df["heart-rate"], errors="coerce")
    df["blood-oxygen"] = pd.to_numeric(df["blood-oxygen"], errors="coerce")
    
    abnormal_heart_rate = df[(df["heart-rate"] > 120) | (df["heart-rate"] < 60) | (df["heart-rate"].isna())]
    abnormal_blood_oxygen = df[(df["blood-oxygen"] < 85) | (df["blood-oxygen"].isna())]

    # **合併異常資料**
    abnormal_data = pd.concat([abnormal_heart_rate, abnormal_blood_oxygen]).drop_duplicates()
    abnormal_data["time"] = abnormal_data["time"].astype(str)

    result_dict = abnormal_data.to_dict(orient="records")
    print("異常數據字典：")
    print(result_dict)
    return result_dict

def llm_handle(info: dict) -> str:
    messages = [
        {"role": "system", "content": "你是一個智能管理助手，專門負責統計異常事件的次數"},
        {"role": "user", "content": f"""
請從以下異常清單中，找出心律在何時出現異常，異常值為何、及血氧在何時出現異常，異常值為何：

異常清單：
{info}
如果找不到異常，請回答沒有異常。
        """}
    ]
    try:
        print("\n呼叫 LLM...")
        
        client = OpenAI(api_key="key")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        response = response.choices[0].message

        print(f"LLM 回應類型: {type(response)}")
        print(f"LLM 原始回應: {response}")

        # 從 content 中提取 JSON
        content = response.content
        print(f"Content: {content}")
        
        # 移除 markdown 代碼塊標記
        content = content.replace('```json', '').replace('```', '').strip()
        print(f"清理後的內容: {content}")
        return content
    except Exception as e:
        print(f"LLM 處理錯誤: {str(e)}")
        return None, 0.0
#tool設定再編輯
@tool
def heart_rate_tool(prompt: str) -> str:

    """獲得心律及血氧的異常數據或檢查心律監測設備的狀態"""
    prompt = prompt.strip()
    sheet = read_google_sheet_heart_rate()
    result_dict = Read_info(sheet)
    output = llm_handle(result_dict)
    return str(output)