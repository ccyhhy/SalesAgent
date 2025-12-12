# crawl_manager.py
# 2025-12-12 最终安全版
# 功能：适配快代理隧道，自动处理认证，V2插件防弹窗

from DrissionPage import ChromiumPage, ChromiumOptions
import time
import urllib.parse
import config  # 读取本地配置
import os
import shutil

class Crawler:
    def __init__(self):
        print("\n🚀 [启动] 正在初始化浏览器...")
        
        co = ChromiumOptions()
        co.no_imgs(True)  # 不加载图片
        co.mute(True)     # 静音
        
        # ============================================================
        # 1. 代理配置 (使用 config 中的变量)
        # ============================================================
        if hasattr(config, 'PROXY_HOST') and config.PROXY_HOST:
            print(f"   📋 读取代理 -> {config.PROXY_HOST}:{config.PROXY_PORT}")
            
            # A. 强制设置代理服务器
            co.set_argument(f'--proxy-server={config.PROXY_HOST}:{config.PROXY_PORT}')
            
            # B. 加载自动认证插件 (Manifest V2 - 彻底解决弹窗)
            if hasattr(config, 'PROXY_USER') and config.PROXY_USER:
                self.plugin_path = self._create_auth_plugin(config.PROXY_USER, config.PROXY_PASS)
                co.add_extension(self.plugin_path)
                print(f"   🔌 [插件] 自动认证模块已加载")
        else:
            print("   ⚠️ 未检测到代理配置，使用直连...")

        # ============================================================
        # 2. 抗干扰配置 (适配校园网/梯子环境)
        # ============================================================
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-gpu')
        co.set_argument('--ignore-certificate-errors')
        
        # 禁用 QUIC 和 WebRTC，防止连接重置和IP泄露
        co.set_argument('--disable-quic')
        co.set_argument('--disable-webrtc')
        
        # 伪装去自动化特征
        co.set_argument('--disable-blink-features=AutomationControlled')

        # 3. 指定用户数据目录
        user_data_path = os.path.join(os.getcwd(), 'browser_data')
        co.set_user_data_path(user_data_path)
        
        try:
            self.page = ChromiumPage(co)
            # 设置 30秒 超时
            self.page.set.timeouts(30)
            
            print(f"   ✅ 浏览器已启动")
            
            # 【自检环节】
            print("   🕵️‍♂️ 正在验证网络...", end="")
            self.page.get('http://httpbin.org/ip', retry=1, show_errmsg=False, timeout=15)
            if "origin" in self.page.html:
                print(" -> 通畅!")
            else:
                print(" -> (无响应，尝试继续)")
            
        except Exception as e:
            print(f"\n   ❌ 启动失败: {e}")
            print("   💡 提示: 校园网用户请确保梯子开启了 [TUN模式] 和 [全局模式]。")

    def _create_auth_plugin(self, user, password):
        """
        生成 Chrome 认证插件 (Manifest V2)
        """
        plugin_path = os.path.join(os.getcwd(), 'proxy_auth_plugin')
        
        # 清理旧插件
        if os.path.exists(plugin_path):
            try: shutil.rmtree(plugin_path)
            except: pass
        os.makedirs(plugin_path)

        # V2 版本 Manifest (最稳)
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy Auth Helper",
            "permissions": [
                "proxy", "tabs", "unlimitedStorage", "storage", 
                "<all_urls>", "webRequest", "webRequestBlocking"
            ],
            "background": { "scripts": ["background.js"] },
            "minimum_chrome_version":"22.0.0"
        }
        """

        # 背景脚本 (需要读取 config 中的 host/port)
        background_js = f"""
        var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{config.PROXY_HOST}",
                    port: parseInt({config.PROXY_PORT})
                }},
                bypassList: ["localhost"]
            }}
        }};

        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

        function callbackFn(details) {{
            return {{
                authCredentials: {{
                    username: "{user}",
                    password: "{password}"
                }}
            }};
        }}

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
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
        """执行搜索和抓取"""
        if not hasattr(self, 'page') or not self.page: return "浏览器未启动"

        print(f"   🔍 搜索: {company_name}...")
        abstract = ""
        website_text = ""
        
        try:
            # 1. 百度搜索
            query = urllib.parse.quote(f"{company_name} 官网")
            self.page.get(f"{config.SEARCH_ENGINE_URL}{query}", retry=3, interval=2, timeout=30)
            
            # 验证码处理
            if "安全验证" in self.page.title or "wappass" in self.page.url:
                print("   ⚠️ 触发验证码，等待 15 秒...")
                time.sleep(15)

            # 抓摘要
            res = self.page.eles('css:#content_left .result', timeout=3)
            for r in res[:3]: abstract += r.text + "\n"

            # 2. 进官网
            target_link = None
            res_list = self.page.eles('css:#content_left .result', timeout=3)
            for res in res_list[:5]:
                title = res.ele('tag:h3').text
                # 排除非官网链接
                if any(x in title for x in ['招聘', '爱企查', '天眼查', '企查查', '58', '百科']):
                    continue
                target_link = res.ele('tag:a')
                break
            
            if target_link:
                print("   🔗 进官网...", end="")
                target_link.click()
                
                self.page.wait.new_tab()
                new_tab = self.page.latest_tab
                
                try:
                    new_tab.wait.ele('tag:body', timeout=20)
                    new_tab.scroll.to_bottom()
                    time.sleep(2)
                    website_text = new_tab.ele('tag:body').text
                    website_text = '\n'.join([l.strip() for l in website_text.split('\n') if l.strip()])
                except:
                    website_text = "官网加载超时"
                
                new_tab.close()
                print(" 完成")
            else:
                print(" (无官网链接)")
                website_text = "未找到官网链接"

        except Exception as e:
            print(f"   ❌ 抓取中断: {e}")
            website_text = f"Error: {e}"

        return f"【百度摘要】\n{abstract}\n\n【官网内容】\n{website_text[:5000]}"

    def close(self):
        try: self.page.quit()
        except: pass