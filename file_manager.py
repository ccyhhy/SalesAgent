import pandas as pd
import config
import os
import datetime

# 【核心修改】在程序启动瞬间，生成一个带时间戳的唯一文件名
# 格式示例：leads_analyzed_20251204_153022.xlsx
current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
DYNAMIC_OUTPUT_FILE = f"leads_analyzed_{current_time}.xlsx"

def load_sop():
    try:
        with open(config.SOP_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ 错误：找不到 {config.SOP_FILE}")
        return None

def init_excel():
    """
    每次启动都是全新的开始，只读取 input 文件
    """
    print(f"📄 本次运行结果将保存为: {DYNAMIC_OUTPUT_FILE}")
    
    if not os.path.exists(config.INPUT_FILE):
        print(f"❌ 错误：找不到输入文件 {config.INPUT_FILE}")
        return None
    
    try:
        df = pd.read_excel(config.INPUT_FILE)
    except Exception as e:
        print(f"❌ 读取 Excel 失败: {e}")
        return None

    if 'COMPANY_NAME' not in df.columns:
        print("❌ 错误：Excel 缺少 COMPANY_NAME 列")
        return None
        
    # 初始化结果列
    for col in ['Is_Target', 'Target_Products', 'Reason']:
        if col not in df.columns:
            df[col] = ""
            
    return df

def save_excel(df):
    """
    保存到带时间戳的新文件中
    """
    try:
        df.to_excel(DYNAMIC_OUTPUT_FILE, index=False)
        return True
    except PermissionError:
        print(f"⚠️ 警告：文件 {DYNAMIC_OUTPUT_FILE} 正被打开，无法保存！")
        return False
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False