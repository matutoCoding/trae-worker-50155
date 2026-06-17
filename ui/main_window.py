import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, close_conn
from ui.batch_page import BatchPage
from ui.outbound_page import OutboundPage
from ui.level_page import LevelPage
from ui.log_page import LogPage


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('检测实验室试剂耗材出入库管理系统')
        self.root.geometry('1200x750')
        self.root.minsize(1024, 680)

        self._setup_style()
        self._create_widgets()

        init_db()

        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Sidebar.TFrame', background='#2c3e50')
        style.configure('SidebarTitle.TLabel',
                        background='#2c3e50',
                        foreground='white',
                        font=('Microsoft YaHei', 14, 'bold'),
                        padding=(0, 20))
        style.configure('NavButton.TButton',
                        font=('Microsoft YaHei', 11),
                        padding=(20, 12),
                        anchor='w')
        style.map('NavButton.TButton',
                  background=[('active', '#34495e'), ('pressed', '#1a252f')],
                  foreground=[('active', 'white'), ('pressed', 'white')])
        style.configure('NavButton.Active.TButton',
                        background='#1890ff',
                        foreground='white',
                        font=('Microsoft YaHei', 11, 'bold'),
                        padding=(20, 12),
                        anchor='w')
        style.configure('Header.TFrame', background='white')
        style.configure('HeaderTitle.TLabel',
                        background='white',
                        foreground='#333',
                        font=('Microsoft YaHei', 16, 'bold'))
        style.configure('HeaderSub.TLabel',
                        background='white',
                        foreground='#666',
                        font=('Microsoft YaHei', 10))
        style.configure('Content.TFrame', background='#f0f2f5')
        style.configure('Card.TFrame', background='white')
        style.configure('CardTitle.TLabel',
                        background='white',
                        foreground='#333',
                        font=('Microsoft YaHei', 12, 'bold'))
        style.configure('StatValue.TLabel',
                        font=('Microsoft YaHei', 20, 'bold'),
                        foreground='#1890ff')
        style.configure('StatLabel.TLabel',
                        font=('Microsoft YaHei', 10),
                        foreground='#666')
        style.configure('Treeview',
                        font=('Microsoft YaHei', 10),
                        rowheight=32)
        style.configure('Treeview.Heading',
                        font=('Microsoft YaHei', 10, 'bold'))
        style.configure('Primary.TButton',
                        font=('Microsoft YaHei', 10),
                        padding=(12, 6))

    def _create_widgets(self):
        main_paned = ttk.PanedWindow(self.root, orient='horizontal')
        main_paned.pack(fill='both', expand=True)

        sidebar = ttk.Frame(main_paned, style='Sidebar.TFrame', width=200)
        sidebar.pack_propagate(False)

        title_label = ttk.Label(sidebar,
                                text='试剂出入库系统',
                                style='SidebarTitle.TLabel')
        title_label.pack()

        ttk.Separator(sidebar, orient='horizontal').pack(fill='x', padx=10)

        self.nav_buttons = {}
        nav_items = [
            ('batch', '🧪  试剂批次'),
            ('outbound', '📦  拆分出库'),
            ('level', '🏆  等级额度'),
            ('log', '📋  变更留痕')
        ]

        for key, label in nav_items:
            btn = ttk.Button(sidebar,
                             text=label,
                             style='NavButton.TButton',
                             command=lambda k=key: self._switch_page(k))
            btn.pack(fill='x', padx=5, pady=2)
            self.nav_buttons[key] = btn

        main_paned.add(sidebar, weight=0)

        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)

        header = ttk.Frame(right_frame, style='Header.TFrame', height=60)
        header.pack_propagate(False)
        header.pack(fill='x')

        self.page_title = ttk.Label(header,
                                    text='试剂批次',
                                    style='HeaderTitle.TLabel')
        self.page_title.pack(side='left', padx=24, pady=15)

        ttk.Label(header,
                  text='检测实验室 · 试剂耗材管理',
                  style='HeaderSub.TLabel').pack(side='right', padx=24, pady=20)

        ttk.Separator(right_frame, orient='horizontal').pack(fill='x')

        self.content_frame = ttk.Frame(right_frame, style='Content.TFrame')
        self.content_frame.pack(fill='both', expand=True)

        self.pages = {}
        self.current_page = None

        self._init_pages()
        self._switch_page('batch')

    def _init_pages(self):
        self.pages['batch'] = BatchPage(self.content_frame)
        self.pages['outbound'] = OutboundPage(self.content_frame)
        self.pages['level'] = LevelPage(self.content_frame)
        self.pages['log'] = LogPage(self.content_frame)

    def _switch_page(self, page_key):
        if self.current_page:
            self.pages[self.current_page].pack_forget()

        self.current_page = page_key
        self.pages[page_key].pack(fill='both', expand=True, padx=16, pady=16)

        titles = {
            'batch': '试剂批次',
            'outbound': '拆分出库',
            'level': '等级额度',
            'log': '变更留痕'
        }
        self.page_title.config(text=titles.get(page_key, ''))

        for key, btn in self.nav_buttons.items():
            if key == page_key:
                btn.config(style='NavButton.Active.TButton')
            else:
                btn.config(style='NavButton.TButton')

        if hasattr(self.pages[page_key], 'refresh'):
            self.pages[page_key].refresh()

    def _on_close(self):
        close_conn()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
