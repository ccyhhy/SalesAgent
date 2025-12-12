from DrissionPage import ChromiumPage, ChromiumOptions
import time
import random
import urllib.parse
import config
import os
import shutil

class Crawler:
    def __init__(self):
        co = ChromiumOptions()
        co.no_imgs(True)
        co.mute(True)
        

        
        # 1. 强制浏览器走代理 (原生参数，最稳，浏览器无法忽略)
        co.set_argument(f'--proxy-server={self.PROXY_HOST}:{self.PROXY_PORT}')
        
        # 2. 加载“只负责填密码”的插件 (解决弹窗问题)
        self.plugin_path = self._create_auth_plugin(self.PROXY_USER, self.PROXY_PASS)
        co.add_extension(self.plugin_path)
        
        # 3. 浏览器记忆
        user_data_path = os.path.join(os.getcwd(), 'browser_data')
        co.set_user_data_path(user_data_path)
        
        try:
            self.page = ChromiumPage(co)
            self.page.set.load_mode.eager()
            print(f"🌐 浏览器已启动 (原生代理+插件认证)")
            
            # 【强制自检】启动时立刻查一次 IP，让你眼见为实
            print("   🕵️‍♂️ 正在验证代理连接...", end="")
            self.page.get('http://httpbin.org/ip', timeout=10)
            # 获取页面显示的 IP
            ip_info = self.page.ele('tag:body').text
            print(f" -> {ip_info}")
            
        except Exception as e:
            print(f"\n❌ 启动自检失败: {e} (可能是代理超时或配置错误)")

    def _create_auth_plugin(self, user, password):
        """
        生成一个【纯粹】的认证插件
        它不再设置代理地址(因为上面用参数设了)，只负责填密码。
        """
        plugin_path = os.path.join(os.getcwd(), 'proxy_auth_plugin')
        
        if os.path.exists(plugin_path):
            shutil.rmtree(plugin_path)
        os.makedirs(plugin_path)

        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 3,
            "name": "Chrome Proxy Auth Helper",
            "permissions": ["proxy", "webRequest", "webRequestBlocking"],
            "host_permissions": ["<all_urls>"],
            "background": {"service_worker": "background.js"}
        }
        """

        # 这个脚本只做一件事：听到要密码，就填进去
        background_js = f"""
        chrome.webRequest.onAuthRequired.addListener(
            function(details) {{
                return {{
                    authCredentials: {{
                        username: "{user}",
                        password: "{password}"
                    }}
                }};
            }},
            {{urls: ["<all_urls>"]}},
            ['blocking']
        );
        """

        with open(os.path.join(plugin_path, "manifest.json"), "w", encoding='utf-8') as f:
            f.write(manifest_json)
        with open(os.path.join(plugin_path, "background.js"), "w", encoding='utf-8') as f:
            f.write(background_js)
        
        return plugin_path

    def search_and_crawl(self, company_name):
        """带重试机制的任务执行"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                return self._execute_task(company_name)
            
            except Exception as e:
                print(f" (⚠️ 异常: {str(e)[:30]}...)")
                
                if attempt < max_retries - 1:
                    print("   🔄 强制重启浏览器换 IP...")
                    self._start_browser() 
                    time.sleep(2)
                else:
                    return f"【失败】多次重试无效"

    def _start_browser(self):
        """重启浏览器逻辑"""
        if self.page:
            try: self.page.quit()
            except: pass
        
        # 重启时必须重新走一遍配置流程
        self.__init__()

    def _execute_task(self, company_name):
        if not self.page or not self.page.process_id:
            raise Exception("浏览器已断开")

        page = self.page
        abstract = ""
        website_text = ""
        
        # --- Step 1: 搜索 ---
        query = urllib.parse.quote(f"{company_name} 官网")
        page.get(f"{config.SEARCH_ENGINE_URL}{query}", retry=1) 
        
        if "安全验证" in page.title or page.ele('text:网络不给力'):
            raise Exception("触发百度验证码") 

        # 抓摘要
        try:
            res = page.eles('css:#content_left .result', timeout=2)
            for r in res[:3]: abstract += r.text + "\n"
        except: pass

        # --- Step 2: 进站 ---
        target_link = None
        try:
            res_list = page.eles('css:#content_left .result', timeout=2)
            for res in res_list[:5]:
                title = res.ele('tag:h3').text
                if any(x in title for x in ['招聘', '爱企查', '天眼查', '企查查', '58同城', '小红书', '知乎', '贴吧', '百科']):
                    continue
                target_link = res.ele('tag:a')
                break
            
            if target_link:
                print("-> 🚀", end="")
                target_link.click()
                page.wait.new_tab()
                new_tab = page.latest_tab
                try:
                    new_tab.wait.ele('tag:body', timeout=10)
                    new_tab.scroll.to_bottom()
                    time.sleep(1)
                    website_text = new_tab.ele('tag:body').text
                    website_text = website_text.replace('\n', ' ')
                except:
                    website_text = "加载超时"
                new_tab.close()
            else:
                print("-> ⚠️", end="")
                website_text = "无官网"
        except:
            if len(page.tabs) > 1: page.latest_tab.close()

        return f"【百度摘要】\n{abstract}\n\n【官网】\n{website_text}"

    def close(self):
        try: self.page.quit()
        except: pass
