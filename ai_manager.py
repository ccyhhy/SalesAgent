# ai_manager.py
from openai import OpenAI
import json
import re
import config

def clean_json_string(content):
    content = re.sub(r'```json\s*', '', content)
    content = re.sub(r'```\s*', '', content)
    return content.strip()

def get_analysis(text_data, system_prompt):
    if "sk-xxxx" in config.API_KEY:
        return {"is_target": False, "reason": "API Key 未配置"}

    client = OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)
    
    try:
        # 【验证点 1】打印您配置的模型
        print(f"   (正在呼叫模型: {config.MODEL_NAME})...", end="")

        response = client.chat.completions.create(
            model=config.MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"【综合文本数据】：{text_data[:30000]}"}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        # 【验证点 2】打印阿里云实际响应的模型 ID
        # 这是最铁的证据，服务器说它用了啥，就是用了啥
        actual_model = response.model
        print(f" -> [服务器确认: {actual_model}]")

        cleaned = clean_json_string(response.choices[0].message.content)
        return json.loads(cleaned)
        
    except Exception as e:
        print(f"\n   ❌ AI 调用失败: {e}")
        return {"is_target": False, "reason": f"AI Error: {str(e)[:50]}"}