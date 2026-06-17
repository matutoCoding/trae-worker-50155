import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import outbound as outbound_db
from database import batch as batch_db
from database import level as level_db


class OutboundPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style='Content.TFrame')
        self.parent = parent
        self.current_page = 1
        self.page_size = 10
        self.total = 0
        self.keyword = tk.StringVar()
        self.selected_batch = tk.StringVar(value='')
        self.batches = []
        self.projects = []

        self._create_widgets()
        self.refresh()

    def _create_widgets(self):
        self._create_stats_card()

        card = tk.Frame(self, bg='white')
        card.pack(fill='both', expand=True, pady=(12, 0))

        header = tk.Frame(card, bg='white')
        header.pack(fill='x', padx=16, pady=12)

        tk.Label(header, text='拆分出库管理',
                 font=('Microsoft YaHei', 12, 'bold'),
                 bg='white', fg='#333').pack(side='left')

        tk.Button(header, text='+ 拆分出库',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=16, pady=6, cursor='hand2',
                  command=self._on_add).pack(side='right')

        search_bar = tk.Frame(card, bg='white')
        search_bar.pack(fill='x', padx=16, pady=(0, 12))

        tk.Entry(search_bar, textvariable=self.keyword,
                 font=('Microsoft YaHei', 10),
                 width=28).pack(side='left', padx=(0, 8))

        self.batch_combo = ttk.Combobox(search_bar, textvariable=self.selected_batch,
                                        width=30, state='readonly')
        self.batch_combo.pack(side='left', padx=(0, 8))

        tk.Button(search_bar, text='查询',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=16, pady=4, cursor='hand2',
                  command=self._on_search).pack(side='left')

        table_frame = tk.Frame(card, bg='white')
        table_frame.pack(fill='both', expand=True, padx=16, pady=(0, 12))

        columns = ['reagent_name', 'quantity', 'project_name', 'receiver',
                   'outbound_date', 'purpose', 'is_hazardous', 'action']
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)

        self.tree.heading('reagent_name', text='试剂名称')
        self.tree.heading('quantity', text='出库数量')
        self.tree.heading('project_name', text='去向/项目')
        self.tree.heading('receiver', text='领取人')
        self.tree.heading('outbound_date', text='出库时间')
        self.tree.heading('purpose', text='用途')
        self.tree.heading('is_hazardous', text='危化品')
        self.tree.heading('action', text='操作')

        self.tree.column('reagent_name', width=150, anchor='w')
        self.tree.column('quantity', width=100, anchor='e')
        self.tree.column('project_name', width=130, anchor='w')
        self.tree.column('receiver', width=90, anchor='w')
        self.tree.column('outbound_date', width=150, anchor='center')
        self.tree.column('purpose', width=100, anchor='w')
        self.tree.column('is_hazardous', width=70, anchor='center')
        self.tree.column('action', width=100, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.tree.tag_configure('hazard', foreground='#f5222d')

        pager = tk.Frame(card, bg='white')
        pager.pack(fill='x', padx=16, pady=(0, 12))

        self.page_info = tk.Label(pager, text='共 0 条',
                                  font=('Microsoft YaHei', 9),
                                  bg='white', fg='#666')
        self.page_info.pack(side='left')

        btn_frame = tk.Frame(pager, bg='white')
        btn_frame.pack(side='right')

        tk.Button(btn_frame, text='上一页',
                  font=('Microsoft YaHei', 9),
                  relief='flat', padx=12, pady=4, cursor='hand2',
                  command=self._prev_page).pack(side='left', padx=2)

        self.page_label = tk.Label(btn_frame, text='第 1 页',
                                   font=('Microsoft YaHei', 9),
                                   bg='white', fg='#333')
        self.page_label.pack(side='left', padx=8)

        tk.Button(btn_frame, text='下一页',
                  font=('Microsoft YaHei', 9),
                  relief='flat', padx=12, pady=4, cursor='hand2',
                  command=self._next_page).pack(side='left', padx=2)

    def _create_stats_card(self):
        stats_frame = tk.Frame(self, bg='white')
        stats_frame.pack(fill='x')

        for i in range(4):
            col = tk.Frame(stats_frame, bg='white')
            col.pack(side='left', fill='x', expand=True, padx=8, pady=12)

        self.stat_today = tk.Label(stats_frame.winfo_children()[0], text='0',
                                   font=('Microsoft YaHei', 18, 'bold'),
                                   bg='white', fg='#1890ff')
        self.stat_today.pack()
        tk.Label(stats_frame.winfo_children()[0], text='今日出库次数',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_month = tk.Label(stats_frame.winfo_children()[1], text='0',
                                   font=('Microsoft YaHei', 18, 'bold'),
                                   bg='white', fg='#fa8c16')
        self.stat_month.pack()
        tk.Label(stats_frame.winfo_children()[1], text='本月出库次数',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_batches = tk.Label(stats_frame.winfo_children()[2], text='0',
                                     font=('Microsoft YaHei', 18, 'bold'),
                                     bg='white', fg='#52c41a')
        self.stat_batches.pack()
        tk.Label(stats_frame.winfo_children()[2], text='在库批次',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_hazard = tk.Label(stats_frame.winfo_children()[3], text='0',
                                    font=('Microsoft YaHei', 18, 'bold'),
                                    bg='white', fg='#f5222d')
        self.stat_hazard.pack()
        tk.Label(stats_frame.winfo_children()[3], text='危化品批次',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

    def refresh(self):
        self._load_batches()
        self._load_projects()

        batch_id = None
        if self.selected_batch.get() and self.batches:
            for b in self.batches:
                if f"{b['reagent_name']} ({b['batch_no']})" == self.selected_batch.get():
                    batch_id = b['id']
                    break

        result = outbound_db.list_outbound(
            keyword=self.keyword.get() or None,
            batch_id=batch_id,
            page=self.current_page,
            page_size=self.page_size
        )

        self.total = result['total']
        data = result['data']

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in data:
            tags = ()
            if row.get('is_hazardous'):
                tags = ('hazard',)

            self.tree.insert('', 'end', values=(
                f"{row['reagent_name']}\n({row['batch_no']})",
                f"{row['quantity']} {row['unit']}",
                row.get('project_name') or '未指定',
                row['receiver'],
                row['outbound_date'],
                row.get('purpose') or '-',
                '是' if row.get('is_hazardous') else '否',
                '分布追踪'
            ), tags=tags)

        self.page_info.config(text=f'共 {self.total} 条记录')
        self.page_label.config(text=f'第 {self.current_page} 页')

        all_result = outbound_db.list_outbound(page=1, page_size=1000)
        all_records = all_result['data']

        today = datetime.now().strftime('%Y-%m-%d')
        today_count = sum(1 for r in all_records
                         if r['outbound_date'].startswith(today))
        self.stat_today.config(text=str(today_count))

        month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        month_count = sum(1 for r in all_records
                         if r['outbound_date'] >= month_start)
        self.stat_month.config(text=str(month_count))

        active_batches = [b for b in self.batches if b['remaining_quantity'] > 0]
        self.stat_batches.config(text=str(len(active_batches)))

        hazard_count = sum(1 for b in self.batches if b['is_hazardous'])
        self.stat_hazard.config(text=str(hazard_count))

    def _load_batches(self):
        result = batch_db.list_batches(page=1, page_size=100)
        self.batches = result['data']
        batch_list = [f"{b['reagent_name']} ({b['batch_no']})" for b in self.batches]
        self.batch_combo['values'] = batch_list

    def _load_projects(self):
        self.projects = level_db.list_projects()

    def _on_search(self):
        self.current_page = 1
        self.refresh()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.refresh()

    def _next_page(self):
        max_page = (self.total + self.page_size - 1) // self.page_size
        if self.current_page < max_page:
            self.current_page += 1
            self.refresh()

    def _on_add(self):
        OutboundDialog(self, batches=self.batches, projects=self.projects,
                       on_success=self.refresh)


class OutboundDialog(tk.Toplevel):
    def __init__(self, parent, batches=None, projects=None, on_success=None):
        super().__init__(parent)
        self.parent = parent
        self.batches = batches or []
        self.projects = projects or []
        self.on_success = on_success
        self.selected_batch_data = None

        self.title('拆分出库')
        self.geometry('500x520')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        form = tk.Frame(self, bg='white')
        form.pack(fill='both', expand=True, padx=20, pady=20)

        self.entries = {}

        tk.Label(form, text='选择试剂批次 *', font=('Microsoft YaHei', 10),
                 bg='white', fg='#333').pack(anchor='w')
        self.batch_var = tk.StringVar()
        self.batch_combo = ttk.Combobox(form, textvariable=self.batch_var,
                                        state='readonly',
                                        values=[f"{b['reagent_name']} ({b['batch_no']}) - 剩余{b['remaining_quantity']}{b['unit']}"
                                                for b in self.batches])
        self.batch_combo.pack(fill='x', pady=(4, 8))
        self.batch_combo.bind('<<ComboboxSelected>>', self._on_batch_select)

        self.batch_info = tk.Frame(form, bg='#f0f7ff', bd=1, relief='solid')
        self.batch_info.pack(fill='x', pady=(0, 12))
        self.batch_info.pack_forget()

        self.info_text = tk.Label(self.batch_info, text='',
                                  font=('Microsoft YaHei', 9),
                                  bg='#f0f7ff', fg='#1890ff',
                                  justify='left', pady=8, padx=12)
        self.info_text.pack(fill='x')

        row1 = tk.Frame(form, bg='white')
        row1.pack(fill='x', pady=6)
        self._add_field(row1, 'quantity', '出库数量 *', 20)
        self._add_field(row1, 'unit_display', '单位', 20)
        self.entries['unit_display'].config(state='disabled')

        tk.Label(form, text='去向项目组 *', font=('Microsoft YaHei', 10),
                 bg='white', fg='#333').pack(anchor='w')
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(form, textvariable=self.project_var,
                                          state='readonly',
                                          values=[f"{p['group_name']} ({p['level_name']})"
                                                  for p in self.projects])
        self.project_combo.pack(fill='x', pady=(4, 8))

        row2 = tk.Frame(form, bg='white')
        row2.pack(fill='x', pady=6)
        self._add_field(row2, 'receiver', '领取人 *', 20)
        self._add_field(row2, 'outbound_date', '出库时间 *', 20)
        self.entries['outbound_date'].insert(0, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        tk.Label(form, text='用途', font=('Microsoft YaHei', 10),
                 bg='white', fg='#333').pack(anchor='w')
        self.entries['purpose'] = tk.Entry(form, font=('Microsoft YaHei', 10))
        self.entries['purpose'].pack(fill='x', pady=(4, 8))

        tk.Label(form, text='备注', font=('Microsoft YaHei', 10),
                 bg='white', fg='#333').pack(anchor='w')
        self.entries['remark'] = tk.Text(form, height=2, font=('Microsoft YaHei', 10))
        self.entries['remark'].pack(fill='x', pady=(4, 0))

        btn_frame = tk.Frame(self, bg='#fafafa')
        btn_frame.pack(fill='x', side='bottom')

        tk.Button(btn_frame, text='取消',
                  font=('Microsoft YaHei', 10),
                  bg='white', fg='#666',
                  activebackground='#f5f5f5',
                  relief='flat', padx=20, pady=8, cursor='hand2',
                  command=self.destroy).pack(side='right', padx=12, pady=12)

        tk.Button(btn_frame, text='确认出库',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=20, pady=8, cursor='hand2',
                  command=self._on_submit).pack(side='right', pady=12)

    def _add_field(self, parent, name, label, width=20):
        field_frame = tk.Frame(parent, bg='white')
        field_frame.pack(side='left', fill='x', expand=True, padx=4)
        tk.Label(field_frame, text=label, font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack(anchor='w')
        entry = tk.Entry(field_frame, font=('Microsoft YaHei', 10))
        entry.pack(fill='x', pady=(4, 0))
        self.entries[name] = entry

    def _on_batch_select(self, event):
        selected = self.batch_var.get()
        for b in self.batches:
            display = f"{b['reagent_name']} ({b['batch_no']}) - 剩余{b['remaining_quantity']}{b['unit']}"
            if display == selected:
                self.selected_batch_data = b
                self.entries['unit_display'].config(state='normal')
                self.entries['unit_display'].delete(0, 'end')
                self.entries['unit_display'].insert(0, b['unit'])
                self.entries['unit_display'].config(state='disabled')

                ratio = b['remaining_quantity'] / b['total_quantity'] * 100
                hazard_text = '是' if b['is_hazardous'] else '否'
                info = (f"总量: {b['total_quantity']} {b['unit']}  |  "
                        f"剩余: {b['remaining_quantity']} {b['unit']} ({ratio:.1f}%)  |  "
                        f"危化品: {hazard_text}")
                if b['is_hazardous'] and b.get('hazard_level'):
                    info += f"\n危险等级: {b['hazard_level']}"

                self.info_text.config(text=info)
                self.batch_info.pack(fill='x', pady=(0, 12))
                break

    def _on_submit(self):
        if not self.selected_batch_data:
            messagebox.showerror('错误', '请选择试剂批次', parent=self)
            return

        quantity = float(self.entries['quantity'].get() or 0)
        if quantity <= 0:
            messagebox.showerror('错误', '出库数量必须大于0', parent=self)
            return

        if quantity > self.selected_batch_data['remaining_quantity']:
            messagebox.showerror('错误',
                                 f'库存不足，当前剩余 {self.selected_batch_data["remaining_quantity"]} {self.selected_batch_data["unit"]}',
                                 parent=self)
            return

        if not self.entries['receiver'].get().strip():
            messagebox.showerror('错误', '请输入领取人', parent=self)
            return

        project_id = None
        project_name = None
        if self.project_var.get():
            for p in self.projects:
                if f"{p['group_name']} ({p['level_name']})" == self.project_var.get():
                    project_id = p['id']
                    project_name = p['group_name']
                    break

        if not project_id:
            messagebox.showerror('错误', '请选择去向项目组', parent=self)
            return

        data = {
            'batch_id': self.selected_batch_data['id'],
            'quantity': quantity,
            'project_id': project_id,
            'project_name': project_name,
            'receiver': self.entries['receiver'].get().strip(),
            'outbound_date': self.entries['outbound_date'].get().strip(),
            'purpose': self.entries['purpose'].get().strip() or None,
            'remark': self.entries['remark'].get('1.0', 'end').strip() or None
        }

        try:
            outbound_db.create_outbound(data)
            messagebox.showinfo('成功', '出库成功', parent=self)
            if self.on_success:
                self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror('错误', str(e), parent=self)
