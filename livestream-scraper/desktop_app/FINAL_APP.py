#!/usr/bin/env python3
"""
FINAL WORKING VERSION (Desktop Mainline)

目标:
1) 从直播间提取手机号 + 用户名
2) UI 全中文
3) 表格列与数据正确对齐
"""

import csv
import json
import os
import queue
import re
import sqlite3
import subprocess
import sys
import threading
import time
import tkinter as tk
import urllib.error
import urllib.request
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional, Tuple

from playwright.sync_api import sync_playwright

try:
    from extractor import LeisuExtractor, ExtractionResult
except ModuleNotFoundError:
    from desktop_app.extractor import LeisuExtractor, ExtractionResult

CHAT_ROW_SELECTORS = [
    "#discussion #msg-list .nano-content ul > li",
    "#msg-list .nano-content ul > li",
    "#msg-list ul > li",
    ".msg-list .nano-content ul > li",
    ".msg-list ul > li",
    "#discussion li.start",
]
CHAT_USERNAME_SELECTORS = [".name", ".username", ".user-name", ".nickname"]
CHAT_MESSAGE_SELECTORS = [".content-txt", ".msg-content", ".content", ".message", ".text"]


def init_db(db_path: str) -> None:
    """初始化本地数据库。"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            formatted TEXT,
            username TEXT,
            context TEXT,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


class FinalApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("雷速直播手机号提取器 - Final v3.1")
        self.root.geometry("1400x920")
        self.root.minsize(1200, 760)

        self.base_dir = self._get_runtime_base_dir()
        self.db_path = os.path.join(self.base_dir, "extracted_phones.db")
        init_db(self.db_path)

        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.found_phones = set()
        self.extractor = LeisuExtractor()
        self.text_output_path = os.path.join(self.base_dir, "phones_user_time.txt")
        self.icon_png_path = self._resolve_icon_path()
        self.icon_photo = None
        self.flush_interval_seconds = 30
        self.last_flush_at = time.time()
        self.pending_flush_count = 0
        self.reconnect_count = 0
        self.text_output_fp = None
        self.log_queue: "queue.Queue[str]" = queue.Queue()
        self.launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ]
        self.cdp_endpoints: List[Tuple[str, str]] = [
            ("Google Chrome", "http://127.0.0.1:9222"),
            ("Microsoft Edge", "http://127.0.0.1:9223"),
            ("Brave", "http://127.0.0.1:9224"),
        ]
        self.cdp_scan_ports = list(range(9222, 9301))
        self.require_normal_browser = True
        self.strict_site_field_mode = True

        self._apply_style()
        self._create_ui()
        self._apply_window_icon()
        self._schedule_log_pump()
        self._load_data()

    def _get_runtime_base_dir(self) -> str:
        """
        返回运行时可持久化目录:
        - exe 模式: exe 所在目录
        - 脚本模式: 当前脚本目录
        """
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def _resolve_icon_path(self) -> str:
        """
        优先使用可访问的图标路径:
        1) 运行目录下 NBF.png
        2) 脚本上级目录 NBF.png
        3) 失败则返回空字符串
        """
        c1 = os.path.join(self.base_dir, "NBF.png")
        c2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "NBF.png"))
        if os.path.exists(c1):
            return c1
        if os.path.exists(c2):
            return c2
        return ""

    def _apply_style(self) -> None:
        """统一样式，避免表格行高/字体错位。"""
        style = ttk.Style()
        style.configure("Treeview", rowheight=28, font=("Microsoft YaHei UI", 10))
        style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"))

    def _apply_window_icon(self) -> None:
        """设置窗口图标（PNG）。"""
        if not self.icon_png_path or not os.path.exists(self.icon_png_path):
            return
        try:
            self.icon_photo = tk.PhotoImage(file=self.icon_png_path)
            self.root.iconphoto(True, self.icon_photo)
        except Exception:
            # 图标设置失败不影响主流程
            pass

    def _create_ui(self) -> None:
        container = ttk.Frame(self.root, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Frame(container)
        header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(
            header, text="雷速直播手机号提取器", font=("Microsoft YaHei UI", 20, "bold")
        ).pack(anchor=tk.W)
        ttk.Label(
            header,
            text="数据来源: live.leisu.com（含主页面与聊天 iframe）",
            font=("Microsoft YaHei UI", 10),
        ).pack(anchor=tk.W, pady=(4, 0))

        # Controls
        ctrl = ttk.Frame(container)
        ctrl.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(ctrl, text="比赛 ID:", font=("Microsoft YaHei UI", 11)).pack(
            side=tk.LEFT
        )
        self.id_var = tk.StringVar(value="4336493")
        ttk.Entry(
            ctrl, textvariable=self.id_var, width=16, font=("Microsoft YaHei UI", 12)
        ).pack(side=tk.LEFT, padx=(6, 10))

        self.btn_start = ttk.Button(ctrl, text="开始提取", command=self._toggle, width=14)
        self.btn_start.pack(side=tk.LEFT, padx=4)

        ttk.Button(ctrl, text="刷新数据", command=self._load_data, width=12).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(ctrl, text="导出 CSV", command=self._export, width=12).pack(
            side=tk.LEFT, padx=4
        )

        # Progress
        self.progress = ttk.Progressbar(container, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(0, 8))
        self.progress.pack_forget()

        # Log
        log_frame = ttk.LabelFrame(container, text="运行日志", padding=6)
        log_frame.pack(fill=tk.X, pady=(0, 8))
        self.log_text = tk.Text(
            log_frame, height=10, wrap=tk.WORD, font=("Consolas", 10), padx=6, pady=6
        )
        self.log_text.pack(fill=tk.X)

        # Table
        table_frame = ttk.LabelFrame(container, text="提取结果", padding=6)
        table_frame.pack(fill=tk.BOTH, expand=True)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        cols = ("id", "phone", "username", "context", "time")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("phone", text="手机号")
        self.tree.heading("username", text="用户名")
        self.tree.heading("context", text="上下文")
        self.tree.heading("time", text="提取时间")

        self.tree.column("id", width=70, anchor="center", stretch=False)
        self.tree.column("phone", width=170, anchor="center", stretch=False)
        self.tree.column("username", width=220, anchor="w")
        self.tree.column("context", width=640, anchor="w")
        self.tree.column("time", width=170, anchor="center", stretch=False)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Stats
        self.stats_var = tk.StringVar(value="总记录: 0 | 本次会话新增: 0")
        ttk.Label(
            container,
            textvariable=self.stats_var,
            font=("Microsoft YaHei UI", 11, "bold"),
            relief=tk.SUNKEN,
            padding=(8, 4),
        ).pack(fill=tk.X, pady=(8, 0))

        self.runtime_var = tk.StringVar(
            value=f"自动落盘: 每{self.flush_interval_seconds}秒 | 下次: {self.flush_interval_seconds}s | 待落盘: 0 | 断线重连: 0"
        )
        ttk.Label(
            container,
            textvariable=self.runtime_var,
            font=("Microsoft YaHei UI", 10),
            relief=tk.SUNKEN,
            padding=(8, 4),
        ).pack(fill=tk.X, pady=(4, 0))

    def log(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        if threading.current_thread() is threading.main_thread():
            self._append_log_line(line)
        else:
            self.log_queue.put(line)
        print(line.strip())

    def _append_log_line(self, line: str) -> None:
        self.log_text.insert(tk.END, line)
        self.log_text.see(tk.END)

    def _schedule_log_pump(self) -> None:
        self._pump_log_queue()
        self.root.after(100, self._schedule_log_pump)

    def _pump_log_queue(self) -> None:
        while True:
            try:
                line = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self._append_log_line(line)

    def _toggle(self) -> None:
        if not self.running:
            self._start()
        else:
            self._stop()

    def _start(self) -> None:
        match_id = self.id_var.get().strip()
        if not match_id:
            messagebox.showerror("错误", "请输入比赛 ID")
            return

        self.running = True
        self.btn_start.config(text="停止提取")
        self.progress.pack(fill=tk.X, pady=(0, 8))
        self.progress.start()
        self.reconnect_count = 0
        self.pending_flush_count = 0
        self.last_flush_at = time.time()
        self._open_text_output()
        self._update_runtime_status()

        self.log("=" * 60)
        self.log(f"开始提取，比赛 ID: {match_id}")
        self.log("=" * 60)
        self.log(f"文本输出文件: {self.text_output_path}")

        self.thread = threading.Thread(target=self._scrape, args=(match_id,), daemon=True)
        self.thread.start()

    def _stop(self) -> None:
        self.running = False
        self.btn_start.config(text="开始提取")
        self.progress.stop()
        self.progress.pack_forget()
        self.log("已请求停止，等待当前轮完成...")

    def _scrape(self, match_id: str) -> None:
        """抓取主流程。"""
        url = f"https://live.leisu.com/detail-{match_id}"
        browser = None
        context = None
        should_close_browser = False

        try:
            with sync_playwright() as p:
                self.log("正在启动浏览器...")
                browser, context, should_close_browser = self._launch_browser_and_context(
                    p
                )
                if browser is None or context is None:
                    self.log(
                        "未连接到可用本机浏览器（真实用户会话）。"
                    )
                    self.log("程序不会自动打开浏览器，只接管你已打开的浏览器实例。")
                    self.log("请先在终端启动本机浏览器后再点击开始：")
                    for line in self._local_browser_launch_hints():
                        self.log(line)
                    return
                context.set_default_timeout(5000)
                page = context.new_page()
                widget_page = None

                self.log(f"打开页面: {url}")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    self.log("页面加载完成")
                except Exception:
                    self.log("页面加载超时，继续尝试提取")

                widget_url = f"https://widget.namitiyu.com/football?id={match_id}"
                try:
                    widget_page = context.new_page()
                    widget_page.goto(widget_url, wait_until="domcontentloaded", timeout=20000)
                    self.log(f"直连聊天页成功: {widget_url}")
                except Exception:
                    self.log("直连聊天页失败，继续主页面+iframe模式")
                    if widget_page:
                        try:
                            widget_page.close()
                        except Exception:
                            pass
                    widget_page = None

                self._wait_chat_ready(page, widget_page)
                self.log("准备进入扫描循环...")
                time.sleep(8)
                self._scrape_loop(page, url, widget_page)

                if widget_page:
                    widget_page.close()

        except Exception as e:
            self.log(f"发生致命错误: {e}")
        finally:
            try:
                if browser:
                    if should_close_browser:
                        browser.close()
                    else:
                        pass  # CDP 模式不主动关闭用户浏览器
            except Exception:
                pass
            self._flush_text_output(force=True)
            self._close_text_output()
            self.running = False
            self.log("提取结束")
            self.root.after(0, self._on_scrape_finished)

    def _on_scrape_finished(self) -> None:
        self.btn_start.config(text="开始提取")
        self.progress.stop()
        self.progress.pack_forget()
        self._update_runtime_status()
        self._load_data()

    def _launch_browser_and_context(
        self, playwright_ctx
    ) -> Tuple[Optional[object], Optional[object], bool]:
        """
        浏览器启动策略:
        1) 优先连接用户已打开的本机浏览器（CDP）
        2) 按要求可禁止任何自动化回退，仅允许本机浏览器会话
        """
        discovered = self._discover_cdp_endpoints()
        if discovered:
            self.log(
                f"检测到可接管浏览器端口: {', '.join([x[1] for x in discovered[:6]])}"
            )

        # 1) 连接已打开的本机浏览器 CDP 端口（真实用户会话）
        for browser_name, cdp_url in discovered:
            try:
                browser = playwright_ctx.chromium.connect_over_cdp(cdp_url)
                if browser and browser.contexts:
                    context = browser.contexts[0]
                else:
                    context = browser.new_context(
                        viewport={"width": 1280, "height": 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    )
                self.log(f"浏览器连接方式: {browser_name} (CDP {cdp_url})")
                return browser, context, False
            except Exception:
                continue

        # 2) 严格模式: 禁止自动化回退
        if self.require_normal_browser:
            self.log("未检测到可连接的本机浏览器 CDP 端口。")
            self.log("当前配置为强制本机浏览器模式，已禁止自动化浏览器回退。")
            self.log("如果浏览器已打开，请先关闭后按命令带 --remote-debugging-port 重新打开。")
            return None, None, False

        return None, None, False

    def _discover_cdp_endpoints(self) -> List[Tuple[str, str]]:
        """
        自动发现“已打开”的本机 Chromium 浏览器 CDP 端口:
        1) 优先固定常用端口
        2) 再扫描 9222-9300 的已监听端口
        """
        candidates: List[Tuple[str, str]] = []
        seen = set()

        # 固定端口优先
        for name, endpoint in self.cdp_endpoints:
            browser_name = self._probe_cdp_browser_name(endpoint)
            if browser_name:
                key = endpoint.lower()
                if key not in seen:
                    seen.add(key)
                    candidates.append((browser_name or name, endpoint))

        # 范围扫描补充（仅探测本机监听端口）
        listen_ports = self._get_listening_ports(self.cdp_scan_ports)
        for port in listen_ports:
            endpoint = f"http://127.0.0.1:{port}"
            key = endpoint.lower()
            if key in seen:
                continue
            browser_name = self._probe_cdp_browser_name(endpoint)
            if browser_name:
                seen.add(key)
                candidates.append((browser_name, endpoint))

        return candidates

    def _get_listening_ports(self, port_candidates: List[int]) -> List[int]:
        """读取本机 TCP 监听端口并与候选集合求交集。"""
        wanted = set(port_candidates)
        found = set()
        try:
            proc = subprocess.run(
                ["netstat", "-ano", "-p", "tcp"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            output = proc.stdout or ""
            for line in output.splitlines():
                line = line.strip()
                if not line.startswith("TCP"):
                    continue
                parts = re.split(r"\s+", line)
                if len(parts) < 4:
                    continue
                local_addr = parts[1]
                state = parts[3].upper()
                if state != "LISTENING":
                    continue
                try:
                    port = int(local_addr.rsplit(":", 1)[-1])
                except ValueError:
                    continue
                if port in wanted:
                    found.add(port)
        except Exception:
            return []
        return sorted(found)

    def _probe_cdp_browser_name(self, endpoint: str) -> str:
        """通过 /json/version 检测是否为可接管的 Chromium CDP 实例。"""
        try:
            url = endpoint.rstrip("/") + "/json/version"
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            info = json.loads(raw)
            browser = str(info.get("Browser", "")).strip()
            ws = str(info.get("webSocketDebuggerUrl", "")).strip()
            if not browser or not ws:
                return ""
            lower = browser.lower()
            if "edg" in lower:
                return "Microsoft Edge"
            if "brave" in lower:
                return "Brave"
            if "chrome" in lower or "chromium" in lower:
                return "Google Chrome"
            return browser
        except (OSError, ValueError, urllib.error.URLError, urllib.error.HTTPError):
            return ""

    def _local_browser_launch_hints(self) -> List[str]:
        """
        输出可直接复制的终端命令:
        - 必须由用户先启动本机浏览器并开启 remote debugging port
        """
        return [
            'Chrome 示例: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="D:\\\\leisu_chrome_profile"',
            'Edge 示例: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe" --remote-debugging-port=9223 --user-data-dir="D:\\\\leisu_edge_profile"',
            'Brave 示例: "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe" --remote-debugging-port=9224 --user-data-dir="D:\\\\leisu_brave_profile"',
            "说明: 必须是已打开浏览器实例启用远程调试端口，程序只接管不会自动启动。",
        ]

    def _scrape_loop(self, page, url: str, widget_page=None) -> None:
        """循环提取，直到停止。"""
        check_count = 0
        rounds_without_new = 0
        rounds_without_chat = 0
        last_chat_row_count = -1

        while self.running:
            try:
                check_count += 1
                self._ensure_chat_tab_active(page, check_count)
                scopes = self._collect_scopes(page, widget_page)
                chat_row_count = sum(self._count_chat_rows(scope) for _, scope in scopes)
                if last_chat_row_count >= 0 and chat_row_count != last_chat_row_count:
                    rounds_without_chat = 0
                else:
                    rounds_without_chat += 1
                last_chat_row_count = chat_row_count

                if check_count % 5 == 1:
                    self.log(
                        f"第 {check_count} 轮扫描，数据域数量: {len(scopes)} | 聊天行数: {chat_row_count}"
                    )

                merged: Dict[str, ExtractionResult] = {}
                for _, scope in scopes:
                    results = self._extract_results(scope)
                    for item in results:
                        best = merged.get(item.phone)
                        if not best or item.confidence > best.confidence:
                            merged[item.phone] = item

                results = list(merged.values())
                new_count = 0

                for result in results:
                    if result.phone in self.found_phones:
                        continue

                    self.found_phones.add(result.phone)
                    username = self._normalize_username(
                        result.username, result.context, result.phone
                    )
                    context = (result.context or "").strip()

                    extracted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self._save(
                        phone=result.phone,
                        formatted=result.phone,
                        username=username,
                        context=context,
                        url=url,
                        extracted_at=extracted_at,
                    )
                    self._append_text_record(
                        phone_11=result.phone,
                        username=username,
                        extracted_at=extracted_at,
                    )
                    new_count += 1
                    self.log(f"发现号码: {result.phone} | 用户: {username}")

                if new_count > 0:
                    rounds_without_new = 0
                    self.root.after(0, self._load_data)
                else:
                    rounds_without_new += 1
                    if check_count % 8 == 0:
                        self.log(
                            f"本轮无新增号码，继续监控...（聊天行数: {chat_row_count}）"
                        )

                for _, scope in scopes:
                    self._safe_scroll(scope)

                # 连续较长时间无新增时，主动重连一次
                if rounds_without_new >= 12:
                    # 仅当聊天区长期空/不可读时才重连，避免“有评论但无新号码”误重连
                    if chat_row_count <= 0 and rounds_without_chat >= 6:
                        self._attempt_reconnect(page, url, "连续多轮无新增且聊天区无数据")
                        rounds_without_new = 0
                        rounds_without_chat = 0
                    else:
                        if check_count % 6 == 1:
                            self.log("检测到聊天区仍有内容，跳过重连")
                        rounds_without_new = 9

                self._flush_text_output()
                self._update_runtime_status()
                time.sleep(4)
            except Exception as e:
                self.log(f"扫描异常: {e}")
                self._attempt_reconnect(page, url, "扫描异常")

    def _wait_chat_ready(self, page, widget_page=None, max_wait_seconds: int = 20) -> None:
        """进入主循环前等待聊天 DOM 就绪，减少首轮计数为 0 的概率。"""
        end_time = time.time() + max_wait_seconds
        round_idx = 0
        while self.running and time.time() < end_time:
            round_idx += 1
            try:
                self._ensure_chat_tab_active(page, round_idx)
            except Exception:
                pass

            scopes = self._collect_scopes(page, widget_page)
            counts = []
            total = 0
            for scope_name, scope in scopes:
                count = self._count_chat_rows(scope)
                counts.append(f"{scope_name}:{count}")
                total += count

            if total > 0:
                self.log(f"聊天区已就绪，行数: {total} ({', '.join(counts)})")
                return

            if round_idx % 3 == 1:
                self.log(f"等待聊天区就绪... ({', '.join(counts) if counts else 'no scope'})")
            time.sleep(0.8)

        self.log("等待聊天区超时，进入扫描循环（将继续尝试提取）。")

    def _ensure_chat_tab_active(self, page, check_count: int) -> None:
        """尽量保持主页面处于“聊天”标签。"""
        try:
            active = page.query_selector("span.txtname.active")
            if active:
                txt = " ".join((active.inner_text() or "").split()).strip()
                if "聊天" in txt:
                    return
        except Exception:
            pass

        click_selectors = [
            "span.txtname:has-text('聊天')",
            "text=聊天",
            "li:has-text('聊天')",
            "button:has-text('聊天')",
        ]
        for selector in click_selectors:
            try:
                node = page.locator(selector).first
                if node.count() > 0:
                    node.click(timeout=1500)
                    if check_count % 6 == 1:
                        self.log("已切换到聊天标签")
                    return
            except Exception:
                continue

    def _is_chat_tab_active(self, scope) -> bool:
        """
        当页面存在 txtname tab 结构时，只有“聊天”激活才允许提取；
        对无该结构的数据域（如部分 iframe）不拦截。
        """
        try:
            has_tabs = scope.query_selector_all("span.txtname")
            if not has_tabs:
                return True
            active = scope.query_selector("span.txtname.active")
            if not active:
                return False
            txt = " ".join((active.inner_text() or "").split()).strip()
            return "聊天" in txt
        except Exception:
            return True

    def _collect_scopes(self, page, widget_page=None) -> List:
        """
        每轮动态收集可提取数据域：
        - 主页面
        - 满足条件的聊天 iframe（可访问时）
        """
        scopes = [("main", page)]
        if widget_page is not None:
            scopes.append(("widget_direct", widget_page))
        try:
            iframes = page.query_selector_all("iframe")
            for idx, iframe in enumerate(iframes):
                try:
                    src = (iframe.get_attribute("src") or "").lower()
                    if not src:
                        continue
                    if (
                        "namitiyu" in src
                        or "widget" in src
                        or "football" in src
                        or "chat" in src
                    ):
                        frame = iframe.content_frame()
                        if frame:
                            scopes.append((f"iframe_{idx}", frame))
                except Exception:
                    continue
        except Exception:
            pass
        return scopes

    def _attempt_reconnect(self, page, url: str, reason: str) -> None:
        """执行一次重连并计数。"""
        self.reconnect_count += 1
        self.log(f"触发重连 #{self.reconnect_count}，原因: {reason}")
        try:
            page.reload(wait_until="domcontentloaded", timeout=30000)
            self.log("重连方式: reload 成功")
        except Exception:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                self.log("重连方式: 重新 goto 成功")
            except Exception:
                self.log("重连失败，将在下一轮重试")
        self._update_runtime_status()
        time.sleep(3)

    def _extract_results(self, scope) -> List[ExtractionResult]:
        """
        从页面/iframe提取手机号和用户名。
        Root cause 修复点:
        - 旧逻辑只用全页正则，几乎拿不到 username。
        - 新逻辑先按“评论元素”提取 username + comment，再交给提取器。
        """
        collected: Dict[str, ExtractionResult] = {}

        # 1) 雷速聊天主结构（实测）
        for item in self._extract_from_leisu_chat_list(scope):
            best = collected.get(item.phone)
            if not best or item.confidence > best.confidence:
                collected[item.phone] = item
        if collected:
            return list(collected.values())

        # 严格字段模式: 仅接受网站明确字段，避免与页面其他文本混淆
        if self.strict_site_field_mode:
            return []

        # 2) 通用评论结构
        container_selectors = [
            "#msg-list ul > li",
            ".msg-list ul > li",
            ".discussionArea .discussion .msg-list ul > li",
            ".comment-item",
            ".chat-item",
            ".message-item",
            ".danmu-item",
            ".live-comment",
            '[class*="comment-list"] > div',
            '[class*="chat-list"] > div',
            '[class*="message-list"] > div',
            ".list-item",
            ".item",
        ]
        username_selectors = [
            ".name",
            ".username",
            ".user-name",
            ".nickname",
            ".nick-name",
            '[class*="user"]',
            '[class*="name"]',
        ]
        message_selectors = [
            ".content-txt",
            ".msg-content",
            ".content",
            ".message",
            ".text",
            ".comment",
            "p",
            "span",
        ]

        for selector in container_selectors:
            try:
                elements = scope.query_selector_all(selector)
            except Exception:
                continue

            if not elements:
                continue

            for elem in elements[:120]:
                username = self._clean_username_text(
                    self._pick_text(elem, username_selectors)
                )
                message = self._pick_text(elem, message_selectors, fallback=True)

                if not username and not message:
                    continue

                extracted = self.extractor.extract_all(username=username, comment=message)
                for item in extracted:
                    best = collected.get(item.phone)
                    if not best or item.confidence > best.confidence:
                        collected[item.phone] = item

            if collected:
                return list(collected.values())

        # Fallback: 整页按行扫描（大概率拿不到用户名，但至少保留上下文）
        try:
            body_text = scope.inner_text("body", timeout=5000)
            for line in body_text.splitlines():
                line = line.strip()
                if not line or len(line) < 6 or len(line) > 220:
                    continue
                # 同时支持纯数字与分隔符号码
                if not re.search(r"1[3-9]\d{9}|1[3-9]\d[\s\-\.]?\d{4}[\s\-\.]?\d{4}", line):
                    continue

                guessed_username = ""
                match_user = re.match(r"^\s*([^\s:：|,，]{2,24})\s*[:：]\s*(.+)$", line)
                if match_user:
                    guessed_username = self._clean_username_text(
                        match_user.group(1).strip()
                    )

                extracted = self.extractor.extract_all(
                    username=guessed_username, comment=line
                )
                for item in extracted:
                    best = collected.get(item.phone)
                    if not best or item.confidence > best.confidence:
                        collected[item.phone] = item
        except Exception:
            pass

        return list(collected.values())

    def _extract_from_leisu_chat_list(self, scope) -> List[ExtractionResult]:
        """
        雷速聊天面板实测结构:
        - 列表: #msg-list / .msg-list 下 ul > li
        - 用户名: .name
        - 消息正文: .content-txt
        """
        selectors = CHAT_ROW_SELECTORS
        username_selectors = CHAT_USERNAME_SELECTORS
        message_selectors = CHAT_MESSAGE_SELECTORS

        collected: Dict[str, ExtractionResult] = {}
        for selector in selectors:
            try:
                items = scope.query_selector_all(selector)
            except Exception:
                continue
            if not items:
                continue

            for elem in items[:320]:
                username = self._clean_username_text(
                    self._pick_text(elem, username_selectors)
                )
                message = self._pick_text(elem, message_selectors, fallback=True)

                if not username and not message:
                    continue

                phones = self._extract_11_digit_phones(f"{username} {message}".strip())
                for phone in phones:
                    extracted = ExtractionResult(
                        phone=phone,
                        formatted_phone=phone,
                        username=username,
                        context=message.strip(),
                        source="comment",
                        confidence=0.99,
                    )
                    best = collected.get(extracted.phone)
                    if not best or extracted.confidence > best.confidence:
                        collected[extracted.phone] = extracted

            if collected:
                return list(collected.values())

        # JS 兜底: 直接从页面执行 querySelectorAll，处理 query_selector_all 偶发失效
        for username, message in self._extract_chat_rows_via_eval(scope):
            phones = self._extract_11_digit_phones(f"{username} {message}".strip())
            for phone in phones:
                extracted = ExtractionResult(
                    phone=phone,
                    formatted_phone=phone,
                    username=self._clean_username_text(username),
                    context=(message or "").strip(),
                    source="comment",
                    confidence=0.99,
                )
                best = collected.get(extracted.phone)
                if not best or extracted.confidence > best.confidence:
                    collected[extracted.phone] = extracted

        return list(collected.values())

    def _extract_11_digit_phones(self, text: str) -> List[str]:
        """从文本中提取并归一化为 11 位手机号。"""
        if not text:
            return []
        phones = set(
            re.findall(r"(?<![0-9A-Za-z])1[3-9]\d{9}(?![0-9A-Za-z])", text)
        )
        for match in re.findall(
            r"(?<![0-9A-Za-z])1[3-9]\d[\s\-\.]?\d{4}[\s\-\.]?\d{4}(?![0-9A-Za-z])",
            text,
        ):
            digits = re.sub(r"[^\d]", "", match)
            if re.fullmatch(r"1[3-9]\d{9}", digits):
                phones.add(digits)
        return sorted(phones)

    def _clean_username_text(self, username: str) -> str:
        """清理用户名里的尾部冒号、空白和明显噪音符号。"""
        if not username:
            return ""
        name = " ".join(username.split()).strip()
        name = re.sub(r"[：:]\s*$", "", name).strip()
        name = re.sub(r"^[\-\|\s]+|[\-\|\s]+$", "", name).strip()
        return name

    def _pick_text(self, elem, selectors: List[str], fallback: bool = False) -> str:
        """从元素内按选择器顺序提取文本。"""
        for selector in selectors:
            try:
                sub = elem.query_selector(selector)
                if not sub:
                    continue
                text = " ".join((sub.inner_text() or "").split())
                if text:
                    return text
            except Exception:
                continue

        if fallback:
            try:
                text = " ".join((elem.inner_text() or "").split())
                return text
            except Exception:
                return ""

        return ""

    def _normalize_username(self, username: str, context: str, phone: str) -> str:
        """标准化用户名，尽量避免 Unknown。"""
        if username and username.strip():
            cleaned = self._clean_username_text(username.strip())
            if cleaned:
                return cleaned

        if context:
            # 尝试从“用户名: 内容含手机号”里猜测用户名
            compact = context.replace(phone, " ").strip()
            m = re.match(r"^([^\s:：|,，]{2,24})\s*[:：]", compact)
            if m:
                candidate = m.group(1).strip()
                if re.search(r"[A-Za-z\u4e00-\u9fff]", candidate):
                    return candidate

            # 尝试从手机号前面的文本抓取用户名
            idx = context.find(phone)
            if idx > 0:
                left = context[max(0, idx - 26) : idx]
                left = re.sub(r"[^\w\u4e00-\u9fff]", " ", left).strip()
                tokens = [t for t in left.split() if t]
                if tokens:
                    candidate = tokens[-1]
                    if 2 <= len(candidate) <= 24 and re.search(
                        r"[A-Za-z\u4e00-\u9fff]", candidate
                    ):
                        return candidate

        return "未知用户"

    def _extract_chat_rows_via_eval(self, scope) -> List[Tuple[str, str]]:
        """通过 JS 直接抓取聊天行文本，作为 DOM API 的兜底路径。"""
        try:
            payload = scope.evaluate(
                """
                ({rowSelectors, usernameSelectors, messageSelectors}) => {
                    const compact = (s) => (s || '').replace(/\\s+/g, ' ').trim();
                    const pick = (root, selectors) => {
                        for (const sel of selectors) {
                            const node = root.querySelector(sel);
                            if (!node) continue;
                            const t = compact(node.innerText || node.textContent || '');
                            if (t) return t;
                        }
                        return '';
                    };
                    const parseRow = (text) => {
                        const t = compact(text);
                        if (!t) return ['', ''];
                        const m = t.match(/^(?:Lv\\s*\\d+\\s*)?(.{1,40}?)[：:](.+)$/);
                        if (!m) return ['', t];
                        return [compact(m[1]), compact(m[2])];
                    };
                    let items = [];
                    for (const sel of rowSelectors) {
                        items = Array.from(document.querySelectorAll(sel));
                        if (items.length) break;
                    }
                    return items.slice(0, 360).map((li) => {
                        let username = pick(li, usernameSelectors);
                        let message = pick(li, messageSelectors);
                        const rowText = compact(li.innerText || li.textContent || '');
                        if ((!username || !message) && rowText) {
                            const [u, m] = parseRow(rowText);
                            if (!username && u) username = u;
                            if (!message && m) message = m;
                        }
                        return [compact(username), compact(message)];
                    }).filter((x) => x[0] || x[1]);
                }
                """,
                {
                    "rowSelectors": CHAT_ROW_SELECTORS,
                    "usernameSelectors": CHAT_USERNAME_SELECTORS,
                    "messageSelectors": CHAT_MESSAGE_SELECTORS,
                },
            )
            if not payload:
                return []
            pairs = []
            for item in payload:
                if not isinstance(item, list) or len(item) < 2:
                    continue
                pairs.append((str(item[0] or ""), str(item[1] or "")))
            return pairs
        except Exception:
            return []

    def _safe_scroll(self, scope) -> None:
        """仅滚动聊天列表容器，避免整页被下拉。"""
        try:
            scope.evaluate(
                """
                () => {
                    const nano = document.querySelector('#msg-list .nano-content, .msg-list .nano-content');
                    if (nano) {
                        nano.scrollTop = nano.scrollHeight;
                        return;
                    }
                    const list = document.querySelector('#msg-list ul, .msg-list ul');
                    if (list && list.parentElement) {
                        list.parentElement.scrollTop = list.parentElement.scrollHeight;
                    }
                }
                """
            )
        except Exception:
            pass

    def _count_chat_rows(self, scope) -> int:
        """统计聊天列表行数，用于判断聊天区是否持续有内容。"""
        selectors = CHAT_ROW_SELECTORS
        max_count = 0
        for selector in selectors:
            try:
                rows = scope.query_selector_all(selector)
                if rows:
                    max_count = max(max_count, len(rows))
            except Exception:
                continue
        if max_count > 0:
            return max_count

        # query_selector_all 没命中时，再用 JS 兜底统计一次
        try:
            result = scope.evaluate(
                """(rowSelectors) => {
                    let maxCount = 0;
                    for (const sel of rowSelectors) {
                        const c = document.querySelectorAll(sel).length;
                        if (c > maxCount) maxCount = c;
                    }
                    return maxCount;
                }""",
                CHAT_ROW_SELECTORS,
            )
            if isinstance(result, int):
                return result
        except Exception:
            pass
        return 0

    def _save(
        self,
        phone: str,
        formatted: str,
        username: str,
        context: str,
        url: str,
        extracted_at: str,
    ) -> None:
        """写入数据库。"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO phones (phone, formatted, username, context, url, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (phone, formatted, username, context, url, extracted_at),
        )
        conn.commit()
        conn.close()

    def _append_text_record(self, phone_11: str, username: str, extracted_at: str) -> None:
        """
        持续追加文本输出，格式: 号码<TAB>名称<TAB>提取时间
        """
        if not self.text_output_fp:
            self._open_text_output()
        if not self.text_output_fp:
            return

        self.text_output_fp.write(f"{phone_11}\t{username}\t{extracted_at}\n")
        self.pending_flush_count += 1

    def _open_text_output(self) -> None:
        """打开文本输出文件，按需写入表头。"""
        os.makedirs(os.path.dirname(self.text_output_path), exist_ok=True)
        need_header = (
            not os.path.exists(self.text_output_path)
            or os.path.getsize(self.text_output_path) == 0
        )
        self.text_output_fp = open(self.text_output_path, "a", encoding="utf-8")
        if need_header:
            self.text_output_fp.write("号码\t名称\t提取时间\n")
        self.last_flush_at = time.time()

    def _flush_text_output(self, force: bool = False) -> None:
        """每 30 秒自动 flush，或强制 flush。"""
        if not self.text_output_fp:
            return

        now = time.time()
        if force or (now - self.last_flush_at >= self.flush_interval_seconds):
            self.text_output_fp.flush()
            try:
                os.fsync(self.text_output_fp.fileno())
            except OSError:
                pass
            self.last_flush_at = now
            if self.pending_flush_count > 0:
                self.log(f"自动落盘完成，本次写入 {self.pending_flush_count} 条")
            self.pending_flush_count = 0
            self._update_runtime_status()

    def _close_text_output(self) -> None:
        """关闭文本输出文件。"""
        if self.text_output_fp:
            try:
                self.text_output_fp.close()
            except Exception:
                pass
            self.text_output_fp = None

    def _update_runtime_status(self) -> None:
        """更新运行状态栏（flush 计时 + 重连计数）。"""
        remain = max(
            0, int(self.flush_interval_seconds - (time.time() - self.last_flush_at))
        )
        text = (
            f"自动落盘: 每{self.flush_interval_seconds}秒 | 下次: {remain}s | "
            f"待落盘: {self.pending_flush_count} | 断线重连: {self.reconnect_count}"
        )
        if hasattr(self, "runtime_var"):
            self.root.after(0, lambda: self.runtime_var.set(text))

    def _load_data(self) -> None:
        """加载数据库到表格。"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM phones ORDER BY id DESC LIMIT 500")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            # 表结构: id, phone, formatted, username, context, url, created_at
            display_phone = re.sub(r"[^\d]", "", row[1] or "")[:11]
            display_username = row[3] or "未知用户"
            display_context = (row[4] or "").replace("\n", " ")
            display_time = (row[6] or "")[:19]

            if len(display_context) > 90:
                display_context = display_context[:90] + "..."

            self.tree.insert(
                "",
                tk.END,
                values=(row[0], display_phone, display_username, display_context, display_time),
            )

        self.stats_var.set(f"总记录: {len(rows)} | 本次会话新增: {len(self.found_phones)}")

    def _export(self) -> None:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"手机号导出_{datetime.now():%Y%m%d_%H%M%S}.csv",
            filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
        )

        if not filepath:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM phones ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()

        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "手机号(11位)", "用户名", "上下文", "来源 URL", "提取时间"])
            for row in rows:
                writer.writerow(
                    [
                        row[0],
                        re.sub(r"[^\d]", "", row[1] or "")[:11],
                        row[3] or "未知用户",
                        (row[4] or "").replace("\n", " "),
                        row[5] or "",
                        row[6] or "",
                    ]
                )

        self.log(f"已导出: {filepath}")
        messagebox.showinfo("导出成功", f"已导出 {len(rows)} 条记录")


def main() -> None:
    root = tk.Tk()
    app = FinalApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
