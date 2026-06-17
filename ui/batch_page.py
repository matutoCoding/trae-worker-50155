import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import batch as batch_db
from database import outbound as outbound_db


class BatchPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style='Content.TFrame')
        self.parent = parent
        self.current_page = 1
        self.page_size = 10
        self.total = 0
        self.keyword = tk.StringVar()
        self.is_hazardous = tk.StringVar(value='')
        self.batch_data_cache = {}

        self._create_widgets()
        self._bind_events()
        self.refresh()

    def _create_widgets(self):
        self._create_stats_card()

        card = tk.Frame(self, bg='white')
        card.pack(fill='both', expand=True, pady=(12, 0))

        header = tk.Frame(card, bg='white')
        header.pack(fill='x', padx=16, pady=12)

        tk.Label(header, text='试剂批次管理',
                 font=('Microsoft YaHei', 12, 'bold'),
                 bg='white', fg='#333').pack(side='left')

        btn_group = tk.Frame(header, bg='white')
        btn_group.pack(side='right')

        tk.Button(btn_group, text='+ 新增批次',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=16, pady=6, cursor='hand2',
                  command=self._on_add).pack(side='right', padx=(8, 0))

        tk.Button(btn_group, text='分布追踪',
                  font=('Microsoft YaHei', 10),
                  bg='#52c41a', fg='white',
                  activebackground='#73d13d', activeforeground='white',
                  relief='flat', padx=12, pady=6, cursor='hand2',
                  command=self._on_distribution).pack(side='right')

        tk.Button(btn_group, text='删除',
                  font=('Microsoft YaHei', 10),
                  bg='#ff4d4f', fg='white',
                  activebackground='#ff7875', activeforeground='white',
                  relief='flat', padx=12, pady=6, cursor='hand2',
                  command=self._on_delete).pack(side='right', padx=(0, 8))

        tk.Button(btn_group, text='编辑',
                  font=('Microsoft YaHei', 10),
                  bg='#fa8c16', fg='white',
                  activebackground='#ffa940', activeforeground='white',
                  relief='flat', padx=12, pady=6, cursor='hand2',
                  command=self._on_edit).pack(side='right')

        search_bar = tk.Frame(card, bg='white')
        search_bar.pack(fill='x', padx=16, pady=(0, 12))

        tk.Entry(search_bar, textvariable=self.keyword,
                 font=('Microsoft YaHei', 10),
                 width=30).pack(side='left', padx=(0, 8))

        hazard_combo = ttk.Combobox(search_bar, textvariable=self.is_hazardous,
                                    values=['', '是', '否'], width=10, state='readonly')
        hazard_combo.pack(side='left', padx=(0, 8))
        hazard_combo.set('')

        tk.Button(search_bar, text='查询',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=16, pady=4, cursor='hand2',
                  command=self._on_search).pack(side='left')

        tk.Label(search_bar, text='（双击行可编辑，右键可查看更多操作）',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#999').pack(side='left', padx=(12, 0))

        table_frame = tk.Frame(card, bg='white')
        table_frame.pack(fill='both', expand=True, padx=16, pady=(0, 12))

        columns = ['reagent_name', 'batch_no', 'specification', 'total_qty',
                   'remaining_qty', 'production_date', 'expiry_date', 'supplier']
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)

        self.tree.heading('reagent_name', text='试剂名称')
        self.tree.heading('batch_no', text='批号')
        self.tree.heading('specification', text='规格')
        self.tree.heading('total_qty', text='总量')
        self.tree.heading('remaining_qty', text='剩余量')
        self.tree.heading('production_date', text='生产日期')
        self.tree.heading('expiry_date', text='有效期至')
        self.tree.heading('supplier', text='供应商')

        self.tree.column('reagent_name', width=150, anchor='w')
        self.tree.column('batch_no', width=130, anchor='w')
        self.tree.column('specification', width=100, anchor='w')
        self.tree.column('total_qty', width=90, anchor='e')
        self.tree.column('remaining_qty', width=120, anchor='e')
        self.tree.column('production_date', width=100, anchor='center')
        self.tree.column('expiry_date', width=110, anchor='center')
        self.tree.column('supplier', width=110, anchor='w')

        vsb = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.tree.tag_configure('low', foreground='#fa8c16')
        self.tree.tag_configure('critical', foreground='#f5222d')
        self.tree.tag_configure('expired', foreground='#f5222d')

        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label='查看详情', command=self._on_detail)
        self.context_menu.add_command(label='编辑', command=self._on_edit)
        self.context_menu.add_command(label='分布追踪', command=self._on_distribution)
        self.context_menu.add_separator()
        self.context_menu.add_command(label='删除', command=self._on_delete)

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

        self.stat_total = tk.Label(stats_frame.winfo_children()[0], text='0',
                                   font=('Microsoft YaHei', 18, 'bold'),
                                   bg='white', fg='#1890ff')
        self.stat_total.pack()
        tk.Label(stats_frame.winfo_children()[0], text='试剂批次总数',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_hazard = tk.Label(stats_frame.winfo_children()[1], text='0',
                                    font=('Microsoft YaHei', 18, 'bold'),
                                    bg='white', fg='#f5222d')
        self.stat_hazard.pack()
        tk.Label(stats_frame.winfo_children()[1], text='危化品批次',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_ok = tk.Label(stats_frame.winfo_children()[2], text='0',
                                font=('Microsoft YaHei', 18, 'bold'),
                                bg='white', fg='#52c41a')
        self.stat_ok.pack()
        tk.Label(stats_frame.winfo_children()[2], text='库存充足',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_warn = tk.Label(stats_frame.winfo_children()[3], text='0',
                                  font=('Microsoft YaHei', 18, 'bold'),
                                  bg='white', fg='#fa8c16')
        self.stat_warn.pack()
        tk.Label(stats_frame.winfo_children()[3], text='库存预警',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

    def _bind_events(self):
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-3>', self._on_right_click)

    def _get_selected_batch(self):
        selection = self.tree.selection()
        if not selection:
            return None
        item_id = selection[0]
        batch_no = self.tree.item(item_id, 'values')[1]
        return self.batch_data_cache.get(item_id)

    def _on_double_click(self, event):
        self._on_edit()

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def refresh(self):
        hazard_val = None
        if self.is_hazardous.get() == '是':
            hazard_val = True
        elif self.is_hazardous.get() == '否':
            hazard_val = False
        else:
            hazard_val = ''

        result = batch_db.list_batches(
            keyword=self.keyword.get() or None,
            is_hazardous=hazard_val,
            page=self.current_page,
            page_size=self.page_size
        )

        self.total = result['total']
        data = result['data']

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.batch_data_cache.clear()

        for row in data:
            ratio = row['remaining_quantity'] / row['total_quantity'] if row['total_quantity'] > 0 else 0
            tag = ''
            if ratio < 0.2:
                tag = 'critical'
            elif ratio < 0.5:
                tag = 'low'

            is_expired = False
            if row['expiry_date']:
                try:
                    exp_date = datetime.strptime(row['expiry_date'], '%Y-%m-%d')
                    if exp_date < datetime.now():
                        is_expired = True
                        tag = 'expired'
                except:
                    pass

            remain_text = f"{row['remaining_quantity']} {row['unit']} ({ratio*100:.1f}%)"
            expiry_text = row['expiry_date'] or '-'
            if is_expired:
                expiry_text = f"{expiry_text} 已过期"

            item_id = self.tree.insert('', 'end', values=(
                row['reagent_name'],
                row['batch_no'],
                row['specification'] or '-',
                f"{row['total_quantity']} {row['unit']}",
                remain_text,
                row['production_date'] or '-',
                expiry_text,
                row['supplier'] or '-'
            ), tags=(tag,) if tag else ())

            self.batch_data_cache[item_id] = row

        self.page_info.config(text=f'共 {self.total} 条记录')
        self.page_label.config(text=f'第 {self.current_page} 页')

        self.stat_total.config(text=str(self.total))
        hazard_count = sum(1 for r in data if r['is_hazardous'])
        self.stat_hazard.config(text=str(hazard_count))
        ok_count = sum(1 for r in data if r['remaining_quantity'] / r['total_quantity'] >= 0.5)
        self.stat_ok.config(text=str(ok_count))
        warn_count = sum(1 for r in data if r['remaining_quantity'] / r['total_quantity'] < 0.2)
        self.stat_warn.config(text=str(warn_count))

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
        BatchDialog(self, mode='add', on_success=self.refresh)

    def _on_edit(self):
        batch = self._get_selected_batch()
        if not batch:
            messagebox.showwarning('提示', '请先选择一个批次', parent=self)
            return
        BatchDialog(self, mode='edit', data=batch, on_success=self.refresh)

    def _on_delete(self):
        batch = self._get_selected_batch()
        if not batch:
            messagebox.showwarning('提示', '请先选择一个批次', parent=self)
            return

        if messagebox.askyesno('确认删除',
                               f'确定要删除试剂批次 "{batch["reagent_name"]} ({batch["batch_no"]})" 吗？\n此操作不可恢复！',
                               parent=self, icon='warning'):
            try:
                batch_db.delete_batch(batch['id'])
                messagebox.showinfo('成功', '删除成功', parent=self)
                self.refresh()
            except Exception as e:
                messagebox.showerror('错误', str(e), parent=self)

    def _on_detail(self):
        batch = self._get_selected_batch()
        if not batch:
            messagebox.showwarning('提示', '请先选择一个批次', parent=self)
            return
        BatchDetailDialog(self, batch)

    def _on_distribution(self):
        batch = self._get_selected_batch()
        if not batch:
            messagebox.showwarning('提示', '请先选择一个批次', parent=self)
            return
        DistributionDialog(self, batch['id'])


class BatchDialog(tk.Toplevel):
    def __init__(self, parent, mode='add', data=None, on_success=None):
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        self.data = data
        self.on_success = on_success

        self.title('新增试剂批次' if mode == 'add' else '编辑试剂批次')
        self.geometry('520x560')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

        if mode == 'edit' and data:
            self._fill_data(data)

    def _create_widgets(self):
        form = tk.Frame(self, bg='white')
        form.pack(fill='both', expand=True, padx=20, pady=20)

        self.entries = {}

        row1 = tk.Frame(form, bg='white')
        row1.pack(fill='x', pady=6)
        self._add_field(row1, 'reagent_name', '试剂名称 *', 20)
        self._add_field(row1, 'batch_no', '批号 *', 20)

        row2 = tk.Frame(form, bg='white')
        row2.pack(fill='x', pady=6)
        self._add_field(row2, 'specification', '规格', 20)
        self._add_field(row2, 'unit', '单位 *', 20)

        row3 = tk.Frame(form, bg='white')
        row3.pack(fill='x', pady=6)
        self._add_field(row3, 'total_quantity', '总数量 *', 20)
        self._add_field(row3, 'supplier', '供应商', 20)

        row4 = tk.Frame(form, bg='white')
        row4.pack(fill='x', pady=6)
        self._add_field(row4, 'production_date', '生产日期 (YYYY-MM-DD)', 20)
        self._add_field(row4, 'expiry_date', '有效期至 (YYYY-MM-DD)', 20)

        row5 = tk.Frame(form, bg='white')
        row5.pack(fill='x', pady=6)
        self._add_field(row5, 'storage_condition', '储存条件', 20)

        row6 = tk.Frame(form, bg='white')
        row6.pack(fill='x', pady=6)
        tk.Label(row6, text='危化品', font=('Microsoft YaHei', 10),
                 bg='white', fg='#333').pack(side='left', padx=(0, 8))
        self.is_hazardous_var = tk.BooleanVar(value=False)
        tk.Checkbutton(row6, variable=self.is_hazardous_var,
                       bg='white', activebackground='white',
                       command=self._on_hazard_toggle).pack(side='left')

        self.hazard_level_frame = tk.Frame(form, bg='white')
        self.hazard_level_frame.pack(fill='x', pady=6)
        self._add_field(self.hazard_level_frame, 'hazard_level', '危险等级', 20)
        self.hazard_level_frame.pack_forget()

        row7 = tk.Frame(form, bg='white')
        row7.pack(fill='x', pady=6)
        tk.Label(row7, text='备注', font=('Microsoft YaHei', 10),
                 bg='white', fg='#333').pack(anchor='w')
        self.entries['remark'] = tk.Text(row7, height=3,
                                          font=('Microsoft YaHei', 10))
        self.entries['remark'].pack(fill='x', pady=(4, 0))

        btn_frame = tk.Frame(self, bg='#fafafa')
        btn_frame.pack(fill='x', side='bottom')

        tk.Button(btn_frame, text='取消',
                  font=('Microsoft YaHei', 10),
                  bg='white', fg='#666',
                  activebackground='#f5f5f5',
                  relief='flat', padx=20, pady=8, cursor='hand2',
                  command=self.destroy).pack(side='right', padx=12, pady=12)

        tk.Button(btn_frame, text='确定',
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

    def _on_hazard_toggle(self):
        if self.is_hazardous_var.get():
            self.hazard_level_frame.pack(fill='x', pady=6)
        else:
            self.hazard_level_frame.pack_forget()

    def _fill_data(self, data):
        self.entries['reagent_name'].insert(0, data.get('reagent_name', ''))
        self.entries['batch_no'].insert(0, data.get('batch_no', ''))
        self.entries['specification'].insert(0, data.get('specification', ''))
        self.entries['unit'].insert(0, data.get('unit', ''))
        self.entries['total_quantity'].insert(0, str(data.get('total_quantity', '')))
        self.entries['supplier'].insert(0, data.get('supplier', ''))
        self.entries['production_date'].insert(0, data.get('production_date') or '')
        self.entries['expiry_date'].insert(0, data.get('expiry_date') or '')
        self.entries['storage_condition'].insert(0, data.get('storage_condition', ''))
        if data.get('is_hazardous'):
            self.is_hazardous_var.set(True)
            self._on_hazard_toggle()
            self.entries['hazard_level'].insert(0, data.get('hazard_level', ''))
        self.entries['remark'].insert('1.0', data.get('remark', ''))

    def _on_submit(self):
        data = {
            'reagent_name': self.entries['reagent_name'].get().strip(),
            'batch_no': self.entries['batch_no'].get().strip(),
            'specification': self.entries['specification'].get().strip() or None,
            'unit': self.entries['unit'].get().strip(),
            'total_quantity': float(self.entries['total_quantity'].get() or 0),
            'supplier': self.entries['supplier'].get().strip() or None,
            'production_date': self.entries['production_date'].get().strip() or None,
            'expiry_date': self.entries['expiry_date'].get().strip() or None,
            'storage_condition': self.entries['storage_condition'].get().strip() or None,
            'is_hazardous': self.is_hazardous_var.get(),
            'hazard_level': self.entries['hazard_level'].get().strip() or None,
            'remark': self.entries['remark'].get('1.0', 'end').strip() or None
        }

        if not data['reagent_name']:
            messagebox.showerror('错误', '请输入试剂名称', parent=self)
            return
        if not data['batch_no']:
            messagebox.showerror('错误', '请输入批号', parent=self)
            return
        if not data['unit']:
            messagebox.showerror('错误', '请输入单位', parent=self)
            return
        if data['total_quantity'] <= 0:
            messagebox.showerror('错误', '总数量必须大于0', parent=self)
            return

        try:
            if self.mode == 'add':
                batch_db.create_batch(data)
                messagebox.showinfo('成功', '新增成功', parent=self)
            else:
                batch_db.update_batch(self.data['id'], data)
                messagebox.showinfo('成功', '修改成功', parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror('错误', str(e), parent=self)


class BatchDetailDialog(tk.Toplevel):
    def __init__(self, parent, batch):
        super().__init__(parent)
        self.parent = parent
        self.batch = batch

        self.title('批次详情')
        self.geometry('600x500')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        container = tk.Frame(self, bg='white')
        container.pack(fill='both', expand=True, padx=20, pady=16)

        tk.Label(container, text=f'{self.batch["reagent_name"]} ({self.batch["batch_no"]})',
                 font=('Microsoft YaHei', 14, 'bold'),
                 bg='white', fg='#333').pack(anchor='w')

        if self.batch.get('is_hazardous'):
            tk.Label(container, text=f'⚠️ 危化品 - {self.batch.get("hazard_level", "未分类")}',
                     font=('Microsoft YaHei', 10),
                     bg='white', fg='#f5222d').pack(anchor='w', pady=(4, 0))

        info_frame = tk.Frame(container, bg='#fafafa', bd=1, relief='solid')
        info_frame.pack(fill='x', pady=12)

        info_data = [
            ('规格', self.batch.get('specification') or '-'),
            ('单位', self.batch.get('unit')),
            ('总数量', f'{self.batch["total_quantity"]} {self.batch["unit"]}'),
            ('剩余量', f'{self.batch["remaining_quantity"]} {self.batch["unit"]}'),
            ('生产日期', self.batch.get('production_date') or '-'),
            ('有效期至', self.batch.get('expiry_date') or '-'),
            ('供应商', self.batch.get('supplier') or '-'),
            ('储存条件', self.batch.get('storage_condition') or '-'),
        ]

        for i, (label, value) in enumerate(info_data):
            row = i // 2
            col = i % 2
            cell = tk.Frame(info_frame, bg='#fafafa')
            cell.grid(row=row, column=col, sticky='ew', padx=12, pady=8)
            cell.grid_columnconfigure(1, weight=1)

            tk.Label(cell, text=label + '：',
                     font=('Microsoft YaHei', 9),
                     bg='#fafafa', fg='#666').grid(row=0, column=0, sticky='w')
            tk.Label(cell, text=str(value),
                     font=('Microsoft YaHei', 10),
                     bg='#fafafa', fg='#333').grid(row=0, column=1, sticky='w')

        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)

        ratio = self.batch['remaining_quantity'] / self.batch['total_quantity'] * 100 if self.batch['total_quantity'] > 0 else 0
        bar_bg = tk.Frame(container, bg='#f0f0f0', height=20)
        bar_bg.pack(fill='x', pady=(0, 4))
        bar_fill = tk.Frame(bar_bg, bg='#52c41a' if ratio >= 50 else '#fa8c16' if ratio >= 20 else '#f5222d',
                            width=max(1, int(ratio * 5.6)), height=20)
        bar_fill.pack(side='left')
        tk.Label(container, text=f'库存剩余 {ratio:.1f}%',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack(anchor='w')

        tk.Label(container, text='出库记录',
                 font=('Microsoft YaHei', 11, 'bold'),
                 bg='white', fg='#333').pack(anchor='w', pady=(16, 8))

        records_frame = tk.Frame(container, bg='white')
        records_frame.pack(fill='both', expand=True)

        columns = ['outbound_date', 'quantity', 'project_name', 'receiver', 'purpose']
        tree = ttk.Treeview(records_frame, columns=columns, show='headings', height=8)

        tree.heading('outbound_date', text='出库时间')
        tree.heading('quantity', text='数量')
        tree.heading('project_name', text='去向项目')
        tree.heading('receiver', text='领取人')
        tree.heading('purpose', text='用途')

        tree.column('outbound_date', width=140, anchor='w')
        tree.column('quantity', width=80, anchor='e')
        tree.column('project_name', width=120, anchor='w')
        tree.column('receiver', width=80, anchor='w')
        tree.column('purpose', width=120, anchor='w')

        vsb = ttk.Scrollbar(records_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        try:
            records = outbound_db.get_outbound_by_batch(self.batch['id'])
            for r in records:
                tree.insert('', 'end', values=(
                    r.get('outbound_date', ''),
                    f"{r['quantity']} {self.batch['unit']}",
                    r.get('project_name') or '-',
                    r.get('receiver', ''),
                    r.get('purpose') or '-'
                ))
        except:
            pass

        btn_frame = tk.Frame(self, bg='#fafafa')
        btn_frame.pack(fill='x', side='bottom')

        tk.Button(btn_frame, text='关闭',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=24, pady=8, cursor='hand2',
                  command=self.destroy).pack(side='right', padx=12, pady=12)


class DistributionDialog(tk.Toplevel):
    def __init__(self, parent, batch_id):
        super().__init__(parent)
        self.parent = parent
        self.batch_id = batch_id

        self.title('批次分布追踪')
        self.geometry('520x520')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        container = tk.Frame(self, bg='white')
        container.pack(fill='both', expand=True, padx=20, pady=16)

        try:
            result = outbound_db.get_distribution(self.batch_id)
            batch = result['batch']
            distribution = result['distribution']
            total_outbound = result['total_outbound']
            unit = batch['unit']
            total_qty = batch['total_quantity']
            remaining = batch['remaining_quantity']
        except Exception as e:
            tk.Label(container, text=f'加载失败：{e}',
                     font=('Microsoft YaHei', 10),
                     bg='white', fg='#f5222d').pack()
            return

        tk.Label(container, text='批次分布追踪',
                 font=('Microsoft YaHei', 14, 'bold'),
                 bg='white', fg='#333').pack(anchor='w')

        summary_frame = tk.Frame(container, bg='#f0f7ff', bd=1, relief='solid')
        summary_frame.pack(fill='x', pady=12)

        stats = [
            ('总数量', f'{total_qty} {unit}', '#1890ff'),
            ('已出库', f'{total_outbound} {unit}', '#fa8c16'),
            ('剩余量', f'{remaining} {unit}', '#52c41a'),
        ]

        for i, (label, value, color) in enumerate(stats):
            col = tk.Frame(summary_frame, bg='#f0f7ff')
            col.pack(side='left', fill='x', expand=True, padx=8, pady=12)
            tk.Label(col, text=label,
                     font=('Microsoft YaHei', 9),
                     bg='#f0f7ff', fg='#666').pack()
            tk.Label(col, text=value,
                     font=('Microsoft YaHei', 14, 'bold'),
                     bg='#f0f7ff', fg=color).pack(pady=(2, 0))

        outbound_ratio = total_outbound / total_qty * 100 if total_qty > 0 else 0
        bar_bg = tk.Frame(container, bg='#f0f0f0', height=18)
        bar_bg.pack(fill='x', pady=(0, 4))

        used_width = max(1, int(outbound_ratio * 4.8))
        tk.Frame(bar_bg, bg='#fa8c16', width=used_width, height=18).pack(side='left')

        tk.Label(container, text=f'已使用 {outbound_ratio:.1f}%，剩余 {100-outbound_ratio:.1f}%',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack(anchor='w', pady=(0, 12))

        tk.Label(container, text='去向好分布',
                 font=('Microsoft YaHei', 11, 'bold'),
                 bg='white', fg='#333').pack(anchor='w', pady=(0, 8))

        list_frame = tk.Frame(container, bg='white')
        list_frame.pack(fill='both', expand=True)

        canvas = tk.Canvas(list_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=canvas.yview)
        items_frame = tk.Frame(canvas, bg='white')

        items_frame.bind('<Configure>',
                         lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=items_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        if distribution:
            for i, item in enumerate(distribution):
                item_frame = tk.Frame(items_frame, bg='white')
                item_frame.pack(fill='x', pady=4)

                header = tk.Frame(item_frame, bg='white')
                header.pack(fill='x')

                tk.Label(header, text=item['destination'],
                         font=('Microsoft YaHei', 10, 'bold'),
                         bg='white', fg='#333').pack(side='left')
                pct = item['total_quantity'] / total_qty * 100 if total_qty > 0 else 0
                tk.Label(header, text=f'{pct:.1f}%',
                         font=('Microsoft YaHei', 10, 'bold'),
                         bg='white', fg='#1890ff').pack(side='right')

                bar_bg = tk.Frame(item_frame, bg='#f0f0f0', height=16)
                bar_bg.pack(fill='x', pady=(4, 2))
                bar_width = max(2, int(pct * 4.8))
                tk.Frame(bar_bg, bg='#1890ff', width=bar_width, height=16).pack(side='left')

                tk.Label(item_frame,
                         text=f"出库 {item['total_quantity']} {unit} · {item['outbound_count']} 次",
                         font=('Microsoft YaHei', 9),
                         bg='white', fg='#999').pack(anchor='w')

                if i < len(distribution) - 1:
                    ttk.Separator(item_frame, orient='horizontal').pack(fill='x', pady=(8, 0))
        else:
            tk.Label(items_frame, text='暂无出库记录',
                     font=('Microsoft YaHei', 10),
                     bg='white', fg='#999').pack(pady=30)

        btn_frame = tk.Frame(self, bg='#fafafa')
        btn_frame.pack(fill='x', side='bottom')

        tk.Button(btn_frame, text='关闭',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=24, pady=8, cursor='hand2',
                  command=self.destroy).pack(side='right', padx=12, pady=12)
