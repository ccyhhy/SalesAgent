import pandas as pd
import config
import file_manager
import crawl_manager
import ai_manager
import time

def main():
    print("🚀 B2B 销售 Agent v10.0 (三态终极版) 启动...")
    print("------------------------------------------------")
    
    # 1. 加载资源
    sop_text = file_manager.load_sop()
    if not sop_text: return

    df = file_manager.init_excel()
    if df is None: return

    # ================= 核心配置 =================
    # 每跑 10 家公司，重启一次浏览器（换IP + 清内存）
    # 如果您觉得代理够稳，可以把这个数字调大，比如 20 或 50
    BATCH_SIZE = 10  
    # ==========================================

    crawler = None
    current_batch_count = 0
    total = len(df)
    
    try:
        for index, row in df.iterrows():
            # 断点续传：如果 Reason 不为空，说明跑过了，跳过
            if pd.notna(row.get('Reason')) and str(row.get('Reason')).strip() != "": 
                continue
            
            company = str(row['COMPANY_NAME']).strip()
            if not company or company == "nan": continue

            # ========================================================
            # 浏览器生命周期管理：启动 或 重启
            # ========================================================
            if crawler is None or current_batch_count >= BATCH_SIZE:
                if crawler: 
                    print(f"\n🔄 [维护] 已跑完 {BATCH_SIZE} 家，重启浏览器以切换 IP/释放内存...")
                    try: crawler.close()
                    except: pass
                    time.sleep(2) # 冷却一下
                else:
                    print(f"\n🔌 [启动] 正在建立连接...")

                crawler = crawl_manager.Crawler()
                current_batch_count = 0 # 计数器归零
            
            # ========================================================

            print(f"[{index+1}/{total}] {company}", end=" ", flush=True)

            try:
                # 1. 爬取
                text_data = crawler.search_and_crawl(company)
                print(" -> 🧠", end="")
                
                # 2. AI 分析
                result = ai_manager.get_analysis(text_data, sop_text)
                
                # 3. 解析状态 (三态逻辑)
                # 优先获取 'status' 字段，如果没有则给默认值 'Review'
                status = result.get('status', 'Review') 
                
                # 兼容性防御：万一 AI 偶尔抽风回了布尔值，做个映射
                if status is True or str(status).lower() == 'true': status = "Target"
                if status is False or str(status).lower() == 'false': status = "Pass"
                
                # 4. 记录结果
                df.at[index, 'Is_Target'] = status
                df.at[index, 'Target_Products'] = str(result.get('target_products', []))
                df.at[index, 'Reason'] = result.get('reason', 'Unknown')
                
                # 5. 终端可视化反馈 (根据状态显示不同图标)
                if status == "Target":
                    icon = "✅" 
                elif status == "Pass":
                    icon = "⬜"
                else:
                    icon = "🤔" # Review (待核实)
                
                print(f" {icon} [{status}]")

                # 6. 实时保存
                file_manager.save_excel(df)
                
                current_batch_count += 1

            except Exception as e:
                print(f"\n   ❌ Error: {e}")
                # 记录错误，防止下次卡在这里死循环（或者您可以选择不记录，让它下次重试）
                df.at[index, 'Reason'] = f"Error: {e}"
                file_manager.save_excel(df)
                
                # 如果报错了，为了安全起见，强制下一次循环重启换IP
                current_batch_count = BATCH_SIZE 

    except KeyboardInterrupt:
        print("\n👋 用户手动停止任务")
    
    finally:
        print("------------------------------------------------")
        print("🎉 任务全部完成！")
        if crawler: 
            try: crawler.close()
            except: pass

if __name__ == "__main__":
    main()