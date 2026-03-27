#!/usr/bin/env python3
"""
Enhanced Live Stream Phone Extractor
高级直播手机号提取器 - 监听WebSocket和API数据

Features:
- 拦截WebSocket消息获取实时聊天数据
- 监听网络请求获取API响应
- 分析页面JavaScript变量
- 多模式手机号匹配
"""

import re
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict

from playwright.async_api import async_playwright, Page


@dataclass
class ExtractionResult:
    """提取结果"""
    phone: str
    formatted: str
    source: str  # 'websocket', 'api', 'dom', 'javascript'
    context: str
    timestamp: str
    url: str = ""


class EnhancedPhoneExtractor:
    """增强版手机号提取器"""
    
    def __init__(self):
        # 标准中国手机号: 1[3-9]xxxxxxxx
        self.patterns = {
            'standard': re.compile(r'1[3-9]\d{9}'),
            'with_separators': re.compile(r'1[3-9]\d[\s\-._]?\d{4}[\s\-._]?\d{4}'),
            'with_prefix': re.compile(r'(?:\+?86)?[\s\-]?1[3-9]\d{9}'),
            'in_text': re.compile(r'(?:电话|手机|联系|微信|☎|Tel|Phone)[:：]?\s*1[3-9]\d{9}'),
            'partial_hidden': re.compile(r'(1[3-9]\d)(\*{3,4})(\d{4})'),
        }
        self.found_phones: Dict[str, ExtractionResult] = {}
        self.network_data: List[Dict] = []
        self.websocket_data: List[Dict] = []
        
    def extract_all_patterns(self, text: str, source: str, url: str = "") -> List[ExtractionResult]:
        """使用所有模式提取手机号"""
        results = []
        if not text or len(text) > 100000:  # 限制文本长度
            return results
            
        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                # 处理元组结果（捕获组）
                if isinstance(match, tuple):
                    if pattern_name == 'partial_hidden':
                        # 部分隐藏的号码: 138****8000 -> 保留以供参考
                        phone = match[0] + match[2]  # 前缀+后缀
                        full_pattern = ''.join(match)
                    else:
                        phone = ''.join(m for m in match if m)
                        full_pattern = phone
                else:
                    phone = match
                    full_pattern = match
                
                # 清理号码
                clean_phone = self._clean_phone(phone)
                
                if self._is_valid_phone(clean_phone) and clean_phone not in self.found_phones:
                    result = ExtractionResult(
                        phone=clean_phone,
                        formatted=self._format_phone(clean_phone),
                        source=f"{source}:{pattern_name}",
                        context=text[:200] if len(text) > 200 else text,
                        timestamp=datetime.now().isoformat(),
                        url=url
                    )
                    results.append(result)
                    self.found_phones[clean_phone] = result
                    
        return results
    
    def _clean_phone(self, phone: str) -> str:
        """清理手机号"""
        clean = re.sub(r'[^\d]', '', phone)
        # 移除国家代码
        if clean.startswith('86') and len(clean) > 11:
            clean = clean[2:]
        return clean
    
    def _is_valid_phone(self, phone: str) -> bool:
        """验证手机号有效性"""
        if len(phone) != 11:
            return False
        if not phone.startswith('1'):
            return False
        if phone[1] not in '3456789':
            return False
        return True
    
    def _format_phone(self, phone: str) -> str:
        """格式化手机号"""
        return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"


class WebSocketInterceptor:
    """WebSocket消息拦截器"""
    
    def __init__(self, extractor: EnhancedPhoneExtractor):
        self.extractor = extractor
        self.messages: List[Dict] = []
        
    def on_websocket_create(self, ws):
        """当WebSocket创建时"""
        print(f"[WebSocket] Created: {ws.url}")
        
        ws.on("framereceived", lambda frame: self._on_message(ws.url, frame, "received"))
        ws.on("framesent", lambda frame: self._on_message(ws.url, frame, "sent"))
        
    def _on_message(self, url: str, frame, direction: str):
        """处理WebSocket消息"""
        try:
            text = frame.text if hasattr(frame, 'text') else str(frame)
            data = {
                'url': url,
                'direction': direction,
                'timestamp': datetime.now().isoformat(),
                'data': text[:1000]  # 限制长度
            }
            self.messages.append(data)
            
            # 尝试提取手机号
            results = self.extractor.extract_all_patterns(text, 'websocket', url)
            for r in results:
                print(f"  📞 [WebSocket] Found: {r.formatted}")
                
        except Exception as e:
            pass  # 忽略解析错误


class NetworkInterceptor:
    """网络请求拦截器"""
    
    def __init__(self, extractor: EnhancedPhoneExtractor):
        self.extractor = extractor
        self.responses: List[Dict] = []
        
    def on_response(self, response):
        """处理HTTP响应"""
        try:
            url = response.url
            
            # 只处理API/JSON响应
            content_type = response.headers.get('content-type', '')
            if 'json' in content_type or 'api' in url:
                try:
                    text = response.text()
                    if len(text) < 500000:  # 限制大小
                        data = {
                            'url': url,
                            'timestamp': datetime.now().isoformat(),
                            'data': text[:2000]
                        }
                        self.responses.append(data)
                        
                        # 提取手机号
                        results = self.extractor.extract_all_patterns(text, 'api', url)
                        for r in results:
                            print(f"  📞 [API] Found: {r.formatted}")
                            
                except:
                    pass
                    
        except Exception as e:
            pass


class EnhancedLiveStreamScraper:
    """增强版直播爬虫"""
    
    def __init__(self, url: str, duration: int = 300):
        self.url = url
        self.duration = duration
        self.extractor = EnhancedPhoneExtractor()
        self.ws_interceptor = WebSocketInterceptor(self.extractor)
        self.net_interceptor = NetworkInterceptor(self.extractor)
        self.running = False
        
    async def run(self):
        """主运行循环"""
        print("=" * 70)
        print("🔍 ENHANCED LIVESTREAM PHONE EXTRACTOR v3.0")
        print("=" * 70)
        print(f"Target: {self.url}")
        print(f"Duration: {self.duration} seconds")
        print("Features: WebSocket监听 | API拦截 | DOM扫描 | JavaScript分析")
        print("=" * 70)
        
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            # 设置拦截器
            await self._setup_interceptors(context)
            
            page = await context.new_page()
            
            try:
                # 导航到页面
                print("\n[1/5] Loading page...")
                await page.goto(self.url, wait_until='networkidle', timeout=30000)
                
                # 等待加载
                print("[2/5] Waiting for content...")
                await asyncio.sleep(5)
                
                # 执行JavaScript分析
                print("[3/5] Analyzing JavaScript variables...")
                await self._analyze_javascript(page)
                
                # 扫描DOM
                print("[4/5] Scanning DOM...")
                await self._scan_dom(page)
                
                # 开始监控
                print("[5/5] Starting real-time monitoring...")
                print("-" * 70)
                await self._monitor(page)
                
            except Exception as e:
                print(f"Error: {e}")
            finally:
                await browser.close()
                
        return self.extractor.found_phones
    
    async def _setup_interceptors(self, context):
        """设置拦截器"""
        # WebSocket拦截
        context.on("websocket", lambda ws: self.ws_interceptor.on_websocket_create(ws))
        
    async def _analyze_javascript(self, page: Page):
        """分析JavaScript变量"""
        try:
            # 获取页面上的所有JavaScript数据
            scripts = await page.query_selector_all('script')
            for script in scripts:
                try:
                    text = await script.inner_text()
                    if text and len(text) < 100000:
                        results = self.extractor.extract_all_patterns(text, 'javascript')
                        for r in results:
                            print(f"  📞 [JS] Found: {r.formatted}")
                except:
                    pass
            
            # 检查window对象中的数据
            js_data = await page.evaluate('''() => {
                const data = {};
                // 常见的数据变量名
                const keys = ['user', 'users', 'data', 'chat', 'comments', 'messages', 
                             'room', 'stream', 'config', 'initData'];
                for (const key of keys) {
                    if (window[key] !== undefined) {
                        try {
                            data[key] = JSON.stringify(window[key]).slice(0, 5000);
                        } catch(e) {}
                    }
                }
                return data;
            }''')
            
            for key, value in js_data.items():
                if value:
                    results = self.extractor.extract_all_patterns(value, f'js:{key}')
                    for r in results:
                        print(f"  📞 [JS:{key}] Found: {r.formatted}")
                        
        except Exception as e:
            print(f"  JavaScript analysis error: {e}")
    
    async def _scan_dom(self, page: Page):
        """扫描DOM"""
        try:
            # 获取整个页面文本
            body_text = await page.inner_text('body')
            results = self.extractor.extract_all_patterns(body_text, 'dom:body')
            for r in results:
                print(f"  📞 [DOM] Found: {r.formatted}")
            
            # 扫描特定元素
            elements = await page.query_selector_all('div, span, p, li, td, a')
            for elem in elements[:200]:  # 限制数量
                try:
                    text = await elem.inner_text()
                    if text and 10 < len(text) < 500:
                        results = self.extractor.extract_all_patterns(text, 'dom:element')
                        for r in results:
                            print(f"  📞 [DOM] Found: {r.formatted}")
                except:
                    continue
                    
        except Exception as e:
            print(f"  DOM scan error: {e}")
    
    async def _monitor(self, page: Page):
        """持续监控"""
        start_time = time.time()
        iteration = 0
        last_count = 0
        
        self.running = True
        while self.running and (time.time() - start_time) < self.duration:
            iteration += 1
            
            # 设置响应拦截（需要在每次导航后重新设置）
            page.on("response", lambda resp: asyncio.create_task(self._handle_response(resp)))
            
            # 滚动页面触发新内容
            if iteration % 3 == 0:
                await page.evaluate('window.scrollBy(0, 800)')
            
            # 定期扫描DOM
            if iteration % 5 == 0:
                await self._quick_scan(page)
            
            # 进度报告
            current_count = len(self.extractor.found_phones)
            if current_count != last_count or iteration % 10 == 0:
                elapsed = int(time.time() - start_time)
                remaining = self.duration - elapsed
                print(f"[{iteration}] ⏱️ {elapsed}s | 📞 {current_count} phones | ⏳ {remaining}s")
                last_count = current_count
            
            await asyncio.sleep(2)
        
        self.running = False
    
    async def _handle_response(self, response):
        """处理响应"""
        self.net_interceptor.on_response(response)
    
    async def _quick_scan(self, page: Page):
        """快速扫描"""
        try:
            body_text = await page.inner_text('body')
            self.extractor.extract_all_patterns(body_text, 'dom:live')
        except:
            pass
    
    def print_summary(self):
        """打印汇总"""
        print("\n" + "=" * 70)
        print("📊 EXTRACTION SUMMARY")
        print("=" * 70)
        print(f"Total unique phones found: {len(self.extractor.found_phones)}")
        
        if self.extractor.found_phones:
            print("\nPhone Numbers:")
            print("-" * 70)
            for i, (phone, data) in enumerate(sorted(self.extractor.found_phones.items()), 1):
                print(f"{i}. {data.formatted}")
                print(f"   Source: {data.source}")
                print(f"   Context: {data.context[:60]}...")
                print()
        else:
            print("\n⚠️ No phone numbers found")
            print("\nPossible reasons:")
            print("- 直播间用户没有在评论中留下手机号")
            print("- 平台对用户数据进行了加密/隐藏")
            print("- 需要登录才能看到更多数据")
            print("- 手机号在图片中而不是文本中")
    
    def save_results(self, filename: str = 'enhanced_phones.json'):
        """保存结果"""
        data = {
            'url': self.url,
            'timestamp': datetime.now().isoformat(),
            'total_found': len(self.extractor.found_phones),
            'phones': {k: asdict(v) for k, v in self.extractor.found_phones.items()}
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Results saved to: {filename}")


async def main():
    """主函数"""
    url = "https://live.leisu.com/detail-4244416"
    
    scraper = EnhancedLiveStreamScraper(url, duration=120)
    try:
        await scraper.run()
    finally:
        scraper.print_summary()
        scraper.save_results()


if __name__ == "__main__":
    asyncio.run(main())
