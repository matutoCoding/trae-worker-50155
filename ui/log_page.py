import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from database import log as log_db
from database import qualification as qual_db
from database import level as level_db
from database import outbound as outbound_db


class LogPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style='Content.TFrame')
        self.parent = parent
        self.current_tab = 'operation'
        self.log_page = 1
        self.log_page_size = 20
        self.log_total = 0
        self.log_module = tk.StringVar(value='')
        self.log_action = tk.StringVar(value='')
        self.log_keyword = tk.StringVar()

        self.qual_page = 1
        self.qual_page_size = 10
        self.qual_total = 0
        self.qual_keyword = tk.StringVar()
        self.qual_status = tk.StringVar(value='')

        self.approval_page = 1
        self.approval_page_size = 20
        self.approval_total = 0
        self.approval_status = tk.StringVar(value='pending')
        self.approval_keyword = tk.StringVar()

        self.projects = []
        self.qual_data_cache = {}
        self.approval_data_cache = {}

        self._create_widgets()
        self._bind_events()
        self.refresh()

    def _create_widgets(self):
        self._create_stats_card()

        card = tk.Frame(self, bg='white')
        card.pack(fill='both', expand=True, pady=(12, 0))

        tab_bar = tk.Frame(card, bg='white')
        tab_bar.pack(fill='x', padx=16, pady=(12, 0))

        self.op_tab = tk.Label(tab_bar, text='📋 操作日志',
                                font=('Microsoft YaHei', 11, 'bold'),
                                bg='white', fg='#1890ff',
                                padx=16, pady=10, cursor='hand2')
        self.op_tab.pack(side='left')
        self.op_tab.bind('<Button-1>', lambda e: self._switch_tab('operation'))

        self.qual_tab = tk.Label(tab_bar, text='⚠️ 危化品资质',
                                  font=('Microsoft YaHei', 11),
                                  bg='white', fg='#666',
                                  padx=16, pady=10, cursor='hand2')
        self.qual_tab.pack(side='left')
        self.qual_tab.bind('<Button-1>', lambda e: self._switch_tab('qualification'))

        self.approval_tab_label_var = tk.StringVar()
        self.approval_tab_label_var.set('📝 出库审批')
        self.approval_tab = tk.Label(tab_bar, textvariable=self.approval_tab_label_var,
                                      font=('Microsoft YaHei', 11),
                                      bg='white', fg='#666',
                                      padx=16, pady=10, cursor='hand2')
        self.approval_tab.pack(side='left')
        self.approval_tab.bind('<Button-1>', lambda e: self._switch_tab('approval'))

        ttk.Separator(card, orient='horizontal').pack(fill='x', pady=(0, 12))

        self.operation_content = tk.Frame(card, bg='white')
        self.qualification_content = tk.Frame(card, bg='white')
        self.approval_content = tk.Frame(card, bg='white')

        self._create_operation_tab()
        self._create_qualification_tab()
        self._create_approval_tab()

        self.operation_content.pack(fill='both', expand=True, padx=16, pady=(0, 12))

    def _create_stats_card(self):
        stats_frame = tk.Frame(self, bg='white')
        stats_frame.pack(fill='x')

        for i in range(7):
            col = tk.Frame(stats_frame, bg='white')
            col.pack(side='left', fill='x', expand=True, padx=4, pady=12)

        self.stat_logs = tk.Label(stats_frame.winfo_children()[0], text='0',
                                  font=('Microsoft YaHei', 18, 'bold'),
                                  bg='white', fg='#1890ff')
        self.stat_logs.pack()
        tk.Label(stats_frame.winfo_children()[0], text='操作日志总数',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_valid = tk.Label(stats_frame.winfo_children()[1], text='0',
                                   font=('Microsoft YaHei', 18, 'bold'),
                                   bg='white', fg='#52c41a')
        self.stat_valid.pack()
        tk.Label(stats_frame.winfo_children()[1], text='有效资质',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_soon = tk.Label(stats_frame.winfo_children()[2], text='0',
                                  font=('Microsoft YaHei', 18, 'bold'),
                                  bg='white', fg='#fa8c16')
        self.stat_soon.pack()
        tk.Label(stats_frame.winfo_children()[2], text='资质即将过期',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_expired = tk.Label(stats_frame.winfo_children()[3], text='0',
                                     font=('Microsoft YaHei', 18, 'bold'),
                                     bg='white', fg='#f5222d')
        self.stat_expired.pack()
        tk.Label(stats_frame.winfo_children()[3], text='资质已过期',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_approval_pending = tk.Label(stats_frame.winfo_children()[4], text='0',
                                              font=('Microsoft YaHei', 18, 'bold'),
                                              bg='white', fg='#f5222d')
        self.stat_approval_pending.pack()
        tk.Label(stats_frame.winfo_children()[4], text='待审批出库',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_approval_approved = tk.Label(stats_frame.winfo_children()[5], text='0',
                                               font=('Microsoft YaHei', 18, 'bold'),
                                               bg='white', fg='#52c41a')
        self.stat_approval_approved.pack()
        tk.Label(stats_frame.winfo_children()[5], text='已通过审批',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_approval_rejected = tk.Label(stats_frame.winfo_children()[6], text='0',
                                               font=('Microsoft YaHei', 18, 'bold'),
                                               bg='white', fg='#8c8c8c')
        self.stat_approval_rejected.pack()
        tk.Label(stats_frame.winfo_children()[6], text='已拒绝审批',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

    def _create_operation_tab(self):
        search_bar = tk.Frame(self.operation_content, bg='white')
        search_bar.pack(fill='x', pady=(0, 12))

        module_combo = ttk.Combobox(search_bar, textvariable=self.log_module,
                                     values=['', '试剂批次', '拆分出库', '等级额度', '危化品资质'],
                                     width=12, state='readonly')
        module_combo.pack(side='left', padx=(0, 8))
        module_combo.set('')

        action_combo = ttk.Combobox(search_bar, textvariable=self.log_action,
                                     values=['', '新增', '修改', '删除', '出库', '升降级'],
                                     width=10, state='readonly')
        action_combo.pack(side='left', padx=(0, 8))
        action_combo.set('')

        tk.Entry(search_bar, textvariable=self.log_keyword,
                 font=('Microsoft YaHei', 10),
                 width=30).pack(side='left', padx=(0, 8))

        tk.Button(search_bar, text='查询',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=16, pady=4, cursor='hand2',
                  command=self._search_logs).pack(side='left')

        table_frame = tk.Frame(self.operation_content, bg='white')
        table_frame.pack(fill='both', expand=True)

        columns = ['created_at', 'module', 'action', 'detail', 'operator']
        self.log_tree = ttk.Treeview(table_frame, columns=columns,
                                      show='headings', height=14)

        self.log_tree.heading('created_at', text='时间')
        self.log_tree.heading('module', text='模块')
        self.log_tree.heading('action', text='操作')
        self.log_tree.heading('detail', text='详情')
        self.log_tree.heading('operator', text='操作人')

        self.log_tree.column('created_at', width=170, anchor='w')
        self.log_tree.column('module', width=100, anchor='center')
        self.log_tree.column('action', width=80, anchor='center')
        self.log_tree.column('detail', width=400, anchor='w')
        self.log_tree.column('operator', width=100, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient='vertical',
                            command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=vsb.set)

        self.log_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        pager = tk.Frame(self.operation_content, bg='white')
        pager.pack(fill='x', pady=(12, 0))

        self.log_page_info = tk.Label(pager, text='共 0 条',
                                      font=('Microsoft YaHei', 9),
                                      bg='white', fg='#666')
        self.log_page_info.pack(side='left')

        btn_frame = tk.Frame(pager, bg='white')
        btn_frame.pack(side='right')

        tk.Button(btn_frame, text='上一页',
                  font=('Microsoft YaHei', 9),
                  relief='flat', padx=12, pady=4, cursor='hand2',
                  command=self._prev_log_page).pack(side='left', padx=2)

        self.log_page_label = tk.Label(btn_frame, text='第 1 页',
                                       font=('Microsoft YaHei', 9),
                                       bg='white', fg='#333')
        self.log_page_label.pack(side='left', padx=8)

        tk.Button(btn_frame, text='下一页',
                  font=('Microsoft YaHei', 9),
                  relief='flat', padx=12, pady=4, cursor='hand2',
                  command=self._next_log_page).pack(side='left', padx=2)

    def _create_qualification_tab(self):
        header = tk.Frame(self.qualification_content, bg='white')
        header.pack(fill='x')

        tk.Label(header, text='危化品资质管理',
                 font=('Microsoft YaHei', 12, 'bold'),
                 bg='white', fg='#333').pack(side='left')

        btn_group = tk.Frame(header, bg='white')
        btn_group.pack(side='right')

        tk.Button(btn_group, text='+ 新增资质',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=16, pady=6, cursor='hand2',
                  command=self._on_add_qual).pack(side='right', padx=(8, 0))

        tk.Button(btn_group, text='删除',
                  font=('Microsoft YaHei', 10),
                  bg='#ff4d4f', fg='white',
                  activebackground='#ff7875', activeforeground='white',
                  relief='flat', padx=12, pady=6, cursor='hand2',
                  command=self._on_delete_qual).pack(side='right', padx=(0, 8))

        tk.Button(btn_group, text='编辑',
                  font=('Microsoft YaHei', 10),
                  bg='#fa8c16', fg='white',
                  activebackground='#ffa940', activeforeground='white',
                  relief='flat', padx=12, pady=6, cursor='hand2',
                  command=self._on_edit_qual).pack(side='right')

        tk.Label(self.qualification_content, text='（双击行可编辑，右键可查看更多操作）',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#999').pack(anchor='w', pady=(8, 0))

        search_bar = tk.Frame(self.qualification_content, bg='white')
        search_bar.pack(fill='x', pady=8)

        tk.Entry(search_bar, textvariable=self.qual_keyword,
                 font=('Microsoft YaHei', 10),
                 width=30).pack(side='left', padx=(0, 8))

        status_combo = ttk.Combobox(search_bar, textvariable=self.qual_status,
                                    values=['', '有效', '过期', '暂停'],
                                    width=10, state='readonly')
        status_combo.pack(side='left', padx=(0, 8))
        status_combo.set('')

        tk.Button(search_bar, text='查询',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=16, pady=4, cursor='hand2',
                  command=self._search_quals).pack(side='left')

        table_frame = tk.Frame(self.qualification_content, bg='white')
        table_frame.pack(fill='both', expand=True)

        columns = ['qual_type', 'cert_no', 'holder', 'project',
                   'expiry', 'status']
        self.qual_tree = ttk.Treeview(table_frame, columns=columns,
                                       show='headings', height=12)

        self.qual_tree.heading('qual_type', text='资质类型')
        self.qual_tree.heading('cert_no', text='证书编号')
        self.qual_tree.heading('holder', text='持有人')
        self.qual_tree.heading('project', text='所属项目')
        self.qual_tree.heading('expiry', text='有效期')
        self.qual_tree.heading('status', text='状态')

        self.qual_tree.column('qual_type', width=180, anchor='w')
        self.qual_tree.column('cert_no', width=160, anchor='w')
        self.qual_tree.column('holder', width=100, anchor='w')
        self.qual_tree.column('project', width=150, anchor='w')
        self.qual_tree.column('expiry', width=140, anchor='center')
        self.qual_tree.column('status', width=80, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient='vertical',
                            command=self.qual_tree.yview)
        self.qual_tree.configure(yscrollcommand=vsb.set)

        self.qual_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.qual_tree.tag_configure('expired', foreground='#f5222d')
        self.qual_tree.tag_configure('warning', foreground='#fa8c16')

        self.qual_context_menu = tk.Menu(self.qual_tree, tearoff=0)
        self.qual_context_menu.add_command(label='编辑', command=self._on_edit_qual)
        self.qual_context_menu.add_separator()
        self.qual_context_menu.add_command(label='删除', command=self._on_delete_qual)

        pager = tk.Frame(self.qualification_content, bg='white')
        pager.pack(fill='x', pady=(12, 0))

        self.qual_page_info = tk.Label(pager, text='共 0 条',
                                       font=('Microsoft YaHei', 9),
                                       bg='white', fg='#666')
        self.qual_page_info.pack(side='left')

        btn_frame = tk.Frame(pager, bg='white')
        btn_frame.pack(side='right')

        tk.Button(btn_frame, text='上一页',
                  font=('Microsoft YaHei', 9),
                  relief='flat', padx=12, pady=4, cursor='hand2',
                  command=self._prev_qual_page).pack(side='left', padx=2)

        self.qual_page_label = tk.Label(btn_frame, text='第 1 页',
                                        font=('Microsoft YaHei', 9),
                                        bg='white', fg='#333')
        self.qual_page_label.pack(side='left', padx=8)

        tk.Button(btn_frame, text='下一页',
                  font=('Microsoft YaHei', 9),
                  relief='flat', padx=12, pady=4, cursor='hand2',
                  command=self._next_qual_page).pack(side='left', padx=2)

    def _switch_tab(self, tab):
        self.current_tab = tab

        tabs = {
            'operation': (self.op_tab, self.operation_content),
            'qualification': (self.qual_tab, self.qualification_content),
            'approval': (self.approval_tab, self.approval_content),
        }

        for name, (tab_lbl, content) in tabs.items():
            if name == tab:
                tab_lbl.config(font=('Microsoft YaHei', 11, 'bold'), fg='#1890ff')
                content.pack(fill='both', expand=True, padx=16, pady=(0, 12))
            else:
                tab_lbl.config(font=('Microsoft YaHei', 11), fg='#666')
                content.pack_forget()

        if tab == 'approval':
            self._load_approvals()

    def _bind_events(self):
        self.qual_tree.bind('<Double-1>', self._on_qual_double_click)
        self.qual_tree.bind('<Button-3>', self._on_qual_right_click)
        self.approval_tree.bind('<Double-1>', self._on_approval_double_click)
        self.approval_tree.bind('<Button-3>', self._on_approval_right_click)

    def _get_selected_qual(self):
        selection = self.qual_tree.selection()
        if not selection:
            return None
        item_id = selection[0]
        return self.qual_data_cache.get(item_id)

    def _on_qual_double_click(self, event):
        self._on_edit_qual()

    def _on_qual_right_click(self, event):
        item = self.qual_tree.identify_row(event.y)
        if item:
            self.qual_tree.selection_set(item)
            self.qual_context_menu.post(event.x_root, event.y_root)

    def _on_edit_qual(self):
        qual = self._get_selected_qual()
        if not qual:
            messagebox.showwarning('提示', '请先选择一条资质记录', parent=self)
            return
        QualificationDialog(self, projects=self.projects, mode='edit',
                            data=qual, on_success=self.refresh)

    def _on_delete_qual(self):
        qual = self._get_selected_qual()
        if not qual:
            messagebox.showwarning('提示', '请先选择一条资质记录', parent=self)
            return
        holder = qual.get('holder_name') or qual.get('certificate_no')
        if messagebox.askyesno('确认删除',
                               f'确定要删除资质 "{qual["qualification_type"]} - {holder}" 吗？\n此操作不可恢复！',
                               parent=self, icon='warning'):
            try:
                qual_db.delete_qualification(qual['id'])
                messagebox.showinfo('成功', '删除成功', parent=self)
                self.refresh()
            except Exception as e:
                messagebox.showerror('错误', str(e), parent=self)

    def refresh(self):
        self._load_logs()
        self._load_quals()
        self.projects = level_db.list_projects()
        if self.current_tab == 'approval':
            self._load_approvals()
        try:
            s = outbound_db.count_approval_stats()
            if s.get('pending', 0) > 0:
                self.approval_tab_label_var.set(f'📝 出库审批 ({s["pending"]})')
            else:
                self.approval_tab_label_var.set('📝 出库审批')
            self.stat_approval_pending.config(text=str(s.get('pending', 0)))
            self.stat_approval_approved.config(text=str(s.get('approved', 0)))
            self.stat_approval_rejected.config(text=str(s.get('rejected', 0)))
        except Exception:
            self.approval_tab_label_var.set('📝 出库审批')
            self.stat_approval_pending.config(text='0')
            self.stat_approval_approved.config(text='0')
            self.stat_approval_rejected.config(text='0')

    def _load_logs(self):
        module_val = self.log_module.get() or None
        action_val = self.log_action.get() or None
        keyword_val = self.log_keyword.get() or None

        result = log_db.list_logs(
            module=module_val,
            action=action_val,
            keyword=keyword_val,
            page=self.log_page,
            page_size=self.log_page_size
        )

        self.log_total = result['total']
        data = result['data']

        for item in self.log_tree.get_children():
            self.log_tree.delete(item)

        for row in data:
            self.log_tree.insert('', 'end', values=(
                row['created_at'],
                row['module'],
                row['action'],
                row.get('detail') or '-',
                row.get('operator') or 'system'
            ))

        self.log_page_info.config(text=f'共 {self.log_total} 条记录')
        self.log_page_label.config(text=f'第 {self.log_page} 页')

        self.stat_logs.config(text=str(self.log_total))

    def _load_quals(self):
        status_map = {'有效': 'valid', '过期': 'expired', '暂停': 'suspended'}
        status_val = status_map.get(self.qual_status.get()) if self.qual_status.get() else None

        result = qual_db.list_qualifications(
            keyword=self.qual_keyword.get() or None,
            status=status_val,
            page=self.qual_page,
            page_size=self.qual_page_size
        )

        self.qual_total = result['total']
        data = result['data']

        for item in self.qual_tree.get_children():
            self.qual_tree.delete(item)
        self.qual_data_cache.clear()

        today = date.today()
        valid_count = 0
        expired_count = 0
        soon_count = 0

        for row in data:
            tags = ()
            is_expired = False
            is_soon = False

            if row.get('expiry_date'):
                try:
                    exp_date = datetime.strptime(row['expiry_date'], '%Y-%m-%d').date()
                    if exp_date < today:
                        is_expired = True
                        tags = ('expired',)
                    elif (exp_date - today).days < 30:
                        is_soon = True
                        tags = ('warning',)
                except:
                    pass

            if row['status'] == 'valid' and not is_expired:
                valid_count += 1
            if is_expired or row['status'] == 'expired':
                expired_count += 1
            if is_soon and not is_expired:
                soon_count += 1

            status_text = row['status']
            if status_text == 'valid':
                status_text = '有效'
            elif status_text == 'expired':
                status_text = '过期'
            elif status_text == 'suspended':
                status_text = '暂停'

            expiry_text = row.get('expiry_date') or '长期有效'
            if is_expired:
                expiry_text += ' (已过期)'
            elif is_soon:
                expiry_text += ' (即将过期)'

            item_id = self.qual_tree.insert('', 'end', values=(
                row['qualification_type'],
                row['certificate_no'],
                row.get('holder_name') or '-',
                row.get('project_name') or '-',
                expiry_text,
                status_text
            ), tags=tags)

            self.qual_data_cache[item_id] = row

        self.qual_page_info.config(text=f'共 {self.qual_total} 条记录')
        self.qual_page_label.config(text=f'第 {self.qual_page} 页')

        try:
            stats = qual_db.count_qual_stats()
            self.stat_valid.config(text=str(stats['valid']))
            self.stat_expired.config(text=str(stats['expired']))
            self.stat_soon.config(text=str(stats['soon']))
        except Exception:
            self.stat_valid.config(text=str(valid_count))
            self.stat_expired.config(text=str(expired_count))
            self.stat_soon.config(text=str(soon_count))

    def _search_logs(self):
        self.log_page = 1
        self._load_logs()

    def _search_quals(self):
        self.qual_page = 1
        self._load_quals()

    def _prev_log_page(self):
        if self.log_page > 1:
            self.log_page -= 1
            self._load_logs()

    def _next_log_page(self):
        max_page = (self.log_total + self.log_page_size - 1) // self.log_page_size
        if self.log_page < max_page:
            self.log_page += 1
            self._load_logs()

    def _prev_qual_page(self):
        if self.qual_page > 1:
            self.qual_page -= 1
            self._load_quals()

    def _next_qual_page(self):
        max_page = (self.qual_total + self.qual_page_size - 1) // self.qual_page_size
        if self.qual_page < max_page:
            self.qual_page += 1
            self._load_quals()

    def _create_approval_tab(self):
        search_bar = tk.Frame(self.approval_content, bg='white')
        search_bar.pack(fill='x', pady=(0, 12))

        status_combo = ttk.Combobox(search_bar, textvariable=self.approval_status,
                                     values=['', 'pending', 'approved', 'rejected'],
                                     width=10, state='readonly')
        status_combo.pack(side='left', padx=(0, 8))
        status_combo.bind('<<ComboboxSelected>>', lambda e: self._search_approvals())

        for s, l in [('', '全部状态'), ('pending', '待审批'), ('approved', '已通过'), ('rejected', '已拒绝')]:
            if self.approval_status.get() == s:
                status_combo.set(l)

        def _fmt_status(val):
            return {'pending': '待审批', 'approved': '已通过', 'rejected': '已拒绝', '': ''}.get(val, val)

        status_map = {'全部状态': '', '待审批': 'pending', '已通过': 'approved', '已拒绝': 'rejected', '': ''}
        status_combo['values'] = ['全部状态', '待审批', '已通过', '已拒绝']
        status_combo.set('待审批')

        tk.Label(search_bar, text='  搜索试剂/项目/批号:',
                 font=('Microsoft YaHei', 10), bg='white', fg='#666').pack(side='left')
        tk.Entry(search_bar, textvariable=self.approval_keyword,
                 font=('Microsoft YaHei', 10),
                 width=30).pack(side='left', padx=(0, 8))

        tk.Button(search_bar, text='查询',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=16, pady=4, cursor='hand2',
                  command=self._search_approvals).pack(side='left')

        table_frame = tk.Frame(self.approval_content, bg='white')
        table_frame.pack(fill='both', expand=True)

        columns = ['created_at', 'reagent', 'batch_no', 'quantity', 'hazard',
                   'project', 'applicant', 'remaining_quota', 'requested', 'shortage',
                   'status', 'note', 'action']
        self.approval_tree = ttk.Treeview(table_frame, columns=columns,
                                           show='headings', height=12)

        headers = [
            ('created_at', '申请时间', 150),
            ('reagent', '试剂名称', 180),
            ('batch_no', '批号', 120),
            ('quantity', '申请数量', 80),
            ('hazard', '类型', 70),
            ('project', '项目组', 150),
            ('applicant', '申请人', 90),
            ('remaining_quota', '剩余额度', 90),
            ('requested', '申请额度', 90),
            ('shortage', '缺口', 80),
            ('status', '审批状态', 80),
            ('note', '审批意见', 200),
            ('action', '操作', 150),
        ]
        for key, text, w in headers:
            self.approval_tree.heading(key, text=text)
            anchor = 'center' if key in ('quantity', 'hazard', 'status') else 'w'
            self.approval_tree.column(key, width=w, anchor=anchor)

        vsb = ttk.Scrollbar(table_frame, orient='vertical',
                            command=self.approval_tree.yview)
        self.approval_tree.configure(yscrollcommand=vsb.set)

        self.approval_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.approval_tree.tag_configure('pending', foreground='#d48806')
        self.approval_tree.tag_configure('approved', foreground='#389e0d')
        self.approval_tree.tag_configure('rejected', foreground='#cf1322')
        self.approval_tree.tag_configure('hazard', background='#fff1f0')

        self.approval_context_menu = tk.Menu(self.approval_tree, tearoff=0)
        self.approval_context_menu.add_command(label='查看详情', command=self._view_approval_detail)
        self.approval_context_menu.add_separator()
        self.approval_context_menu.add_command(label='通过审批', command=self._approve_approval)
        self.approval_context_menu.add_command(label='拒绝审批', command=self._reject_approval)

        pager = tk.Frame(self.approval_content, bg='white')
        pager.pack(fill='x', pady=(12, 0))

        self.approval_page_info = tk.Label(pager, text='共 0 条',
                                           font=('Microsoft YaHei', 9),
                                           bg='white', fg='#666')
        self.approval_page_info.pack(side='left')

        btn_frame = tk.Frame(pager, bg='white')
        btn_frame.pack(side='right')

        tk.Button(btn_frame, text='上一页',
                  font=('Microsoft YaHei', 9),
                  relief='flat', padx=12, pady=4, cursor='hand2',
                  command=self._prev_approval_page).pack(side='left', padx=2)

        self.approval_page_label = tk.Label(btn_frame, text='第 1 页',
                                             font=('Microsoft YaHei', 9),
                                             bg='white', fg='#333')
        self.approval_page_label.pack(side='left', padx=8)

        tk.Button(btn_frame, text='下一页',
                  font=('Microsoft YaHei', 9),
                  relief='flat', padx=12, pady=4, cursor='hand2',
                  command=self._next_approval_page).pack(side='left', padx=2)

    def _search_approvals(self):
        self.approval_page = 1
        self._load_approvals()

    def _prev_approval_page(self):
        if self.approval_page > 1:
            self.approval_page -= 1
            self._load_approvals()

    def _next_approval_page(self):
        max_page = (self.approval_total + self.approval_page_size - 1) // self.approval_page_size
        if self.approval_page < max_page:
            self.approval_page += 1
            self._load_approvals()

    def _load_approvals(self):
        for row in self.approval_tree.get_children():
            self.approval_tree.delete(row)
        self.approval_data_cache = {}

        status_display_to_val = {'全部状态': None, '待审批': 'pending',
                                  '已通过': 'approved', '已拒绝': 'rejected', '': None}
        status_val = status_display_to_val.get(self.approval_status.get())
        keyword = self.approval_keyword.get().strip() or None

        try:
            result = outbound_db.list_outbound_approvals(
                status=status_val, project_id=None, keyword=keyword,
                page=self.approval_page, page_size=self.approval_page_size
            )
        except Exception as e:
            messagebox.showerror('错误', f'加载审批列表失败：{e}', parent=self)
            return

        records = result.get('records', [])
        total = result.get('total', 0)
        self.approval_total = total

        status_display = {'pending': '待审批', 'approved': '已通过', 'rejected': '已拒绝'}

        for r in records:
            tags = [r['status']]
            if r.get('is_hazardous'):
                tags.append('hazard')

            action_text = ''
            if r['status'] == 'pending':
                action_text = '通过 | 拒绝'
            elif r['status'] == 'approved':
                action_text = f"通过 {r.get('approved_by', '')} {r.get('approved_at', '')[:10]}"
            elif r['status'] == 'rejected':
                action_text = f"拒绝 {r.get('approved_by', '')} {r.get('approved_at', '')[:10]}"

            vals = (
                r.get('created_at', '')[:19] if r.get('created_at') else '',
                r.get('reagent_name', '') or '',
                r.get('batch_no', '') or '',
                f"{r.get('quantity', 0)} {r.get('unit', '')}",
                '⚠️危化' if r.get('is_hazardous') else '普通',
                r.get('project_name', '') or '',
                r.get('applicant', '') or '',
                f"{r.get('remaining_quota', 0):.1f}",
                f"{r.get('requested_amount', 0):.1f}",
                f"{r.get('quota_shortage', 0):.1f}",
                status_display.get(r['status'], r['status']),
                r.get('approval_note', '') or '',
                action_text,
            )
            item = self.approval_tree.insert('', 'end', values=vals, tags=tags)
            self.approval_data_cache[item] = r

        self.approval_page_info.config(text=f'共 {total} 条')
        max_page = max(1, (total + self.approval_page_size - 1) // self.approval_page_size)
        self.approval_page_label.config(text=f'第 {self.approval_page} / {max_page} 页')

    def _get_selected_approval(self):
        selection = self.approval_tree.selection()
        if not selection:
            messagebox.showwarning('提示', '请先选择一条审批记录', parent=self)
            return None
        item = selection[0]
        return self.approval_data_cache.get(item)

    def _on_approval_double_click(self, event):
        self._view_approval_detail()

    def _on_approval_right_click(self, event):
        item = self.approval_tree.identify_row(event.y)
        if item:
            self.approval_tree.selection_set(item)
            self.approval_context_menu.post(event.x_root, event.y_root)

    def _view_approval_detail(self):
        r = self._get_selected_approval()
        if not r:
            return
        ApprovalDetailDialog(self, approval=r)

    def _approve_approval(self):
        r = self._get_selected_approval()
        if not r:
            return
        if r['status'] != 'pending':
            messagebox.showwarning('提示', '只有待审批状态的记录可以通过', parent=self)
            return
        ApprovalActionDialog(self, approval=r, action='approve',
                             on_success=self.refresh)

    def _reject_approval(self):
        r = self._get_selected_approval()
        if not r:
            return
        if r['status'] != 'pending':
            messagebox.showwarning('提示', '只有待审批状态的记录可以拒绝', parent=self)
            return
        ApprovalActionDialog(self, approval=r, action='reject',
                             on_success=self.refresh)

    def _on_add_qual(self):
        QualificationDialog(self, projects=self.projects, mode='add',
                            on_success=self.refresh)


class QualificationDialog(tk.Toplevel):
    def __init__(self, parent, projects=None, mode='add', data=None, on_success=None):
        super().__init__(parent)
        self.parent = parent
        self.projects = projects or []
        self.mode = mode
        self.data = data
        self.on_success = on_success

        self.title('新增资质' if mode == 'add' else '编辑资质')
        self.geometry('500x520')
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

        tk.Label(row1, text='资质类型 *', font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack(anchor='w')
        self.qual_type_var = tk.StringVar()
        type_combo = ttk.Combobox(row1, textvariable=self.qual_type_var,
                                  values=['危险化学品安全管理人员', '危险化学品操作人员',
                                          '剧毒化学品使用资质', '易制毒化学品使用资质', '其他'])
        type_combo.pack(fill='x', pady=(4, 0))

        self._add_field(form, 'certificate_no', '证书编号 *')

        tk.Label(form, text='所属项目组', font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack(anchor='w', pady=(6, 0))
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(form, textvariable=self.project_var,
                                          state='readonly',
                                          values=[p['group_name'] for p in self.projects])
        self.project_combo.pack(fill='x', pady=(4, 0))

        row2 = tk.Frame(form, bg='white')
        row2.pack(fill='x', pady=6)
        self._add_field(row2, 'holder_name', '持有人姓名', 20)
        self._add_field(row2, 'holder_id_card', '身份证号', 20)

        row3 = tk.Frame(form, bg='white')
        row3.pack(fill='x', pady=6)
        self._add_field(row3, 'issue_date', '发证日期', 20)
        self._add_field(row3, 'expiry_date', '有效期至', 20)

        self._add_field(form, 'issuing_authority', '发证机关')

        tk.Label(form, text='状态', font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack(anchor='w', pady=(6, 0))
        self.status_var = tk.StringVar(value='有效')
        status_combo = ttk.Combobox(form, textvariable=self.status_var,
                                     values=['有效', '过期', '暂停'],
                                     state='readonly')
        status_combo.pack(fill='x', pady=(4, 0))

        tk.Label(form, text='备注', font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack(anchor='w', pady=(6, 0))
        self.entries['remark'] = tk.Text(form, height=2,
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

    def _fill_data(self, data):
        self.qual_type_var.set(data.get('qualification_type', ''))
        self.entries['certificate_no'].insert(0, data.get('certificate_no', ''))
        self.entries['holder_name'].insert(0, data.get('holder_name') or '')
        self.entries['holder_id_card'].insert(0, data.get('holder_id_card') or '')
        self.entries['issue_date'].insert(0, data.get('issue_date') or '')
        self.entries['expiry_date'].insert(0, data.get('expiry_date') or '')
        self.entries['issuing_authority'].insert(0, data.get('issuing_authority') or '')
        self.entries['remark'].insert('1.0', data.get('remark') or '')

        status_map = {'valid': '有效', 'expired': '过期', 'suspended': '暂停'}
        self.status_var.set(status_map.get(data.get('status', 'valid'), '有效'))

        if data.get('project_name'):
            self.project_var.set(data['project_name'])

    def _on_submit(self):
        qual_type = self.qual_type_var.get().strip()
        cert_no = self.entries['certificate_no'].get().strip()

        if not qual_type:
            messagebox.showerror('错误', '请选择或输入资质类型', parent=self)
            return
        if not cert_no:
            messagebox.showerror('错误', '请输入证书编号', parent=self)
            return

        project_id = None
        project_name = None
        if self.project_var.get():
            for p in self.projects:
                if p['group_name'] == self.project_var.get():
                    project_id = p['id']
                    project_name = p['group_name']
                    break

        status_map = {'有效': 'valid', '过期': 'expired', '暂停': 'suspended'}

        data = {
            'qualification_type': qual_type,
            'certificate_no': cert_no,
            'project_id': project_id,
            'project_name': project_name,
            'holder_name': self.entries['holder_name'].get().strip() or None,
            'holder_id_card': self.entries['holder_id_card'].get().strip() or None,
            'issue_date': self.entries['issue_date'].get().strip() or None,
            'expiry_date': self.entries['expiry_date'].get().strip() or None,
            'issuing_authority': self.entries['issuing_authority'].get().strip() or None,
            'status': status_map.get(self.status_var.get(), 'valid'),
            'remark': self.entries['remark'].get('1.0', 'end').strip() or None
        }

        try:
            if self.mode == 'add':
                qual_db.create_qualification(data)
                messagebox.showinfo('成功', '新增成功', parent=self)
            else:
                qual_db.update_qualification(self.data['id'], data)
                messagebox.showinfo('成功', '修改成功', parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror('错误', str(e), parent=self)


class ApprovalDetailDialog(tk.Toplevel):
    def __init__(self, parent, approval=None):
        super().__init__(parent)
        self.parent = parent
        self.approval = approval
        self.title('出库审批详情')
        self.geometry('560x560')
        self.configure(bg='#f0f2f5')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        card = tk.Frame(self, bg='white')
        card.pack(fill='both', expand=True, padx=16, pady=16)

        status_display = {'pending': '待审批', 'approved': '已通过', 'rejected': '已拒绝'}
        status_color = {'pending': '#d48806', 'approved': '#389e0d', 'rejected': '#cf1322'}

        r = self.approval or {}

        title = f"出库审批 #{r.get('id', '')}"
        tk.Label(card, text=title,
                 font=('Microsoft YaHei', 15, 'bold'),
                 bg='white', fg='#262626').pack(anchor='w', padx=20, pady=(16, 4))
        tk.Label(card,
                 text=f"申请时间：{r.get('created_at', '')}    申请人：{r.get('applicant', '')}",
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#8c8c8c').pack(anchor='w', padx=20)

        st = r.get('status', 'pending')
        tk.Label(card, text=f"状态：{status_display.get(st, st)}",
                 font=('Microsoft YaHei', 11, 'bold'),
                 bg='white', fg=status_color.get(st, '#262626')).pack(anchor='w', padx=20, pady=(8, 0))

        ttk.Separator(card, orient='horizontal').pack(fill='x', padx=20, pady=14)

        info_frame = tk.Frame(card, bg='white')
        info_frame.pack(fill='x', padx=20)

        fields = [
            ('试剂名称', r.get('reagent_name', '')),
            ('批号', r.get('batch_no', '')),
            ('类型', '⚠️ 危化品' if r.get('is_hazardous') else '普通试剂'),
            ('申请数量', f"{r.get('quantity', 0)} {r.get('unit', '')}"),
            ('项目组', r.get('project_name', '')),
            ('领取人', r.get('receiver', '')),
            ('出库日期', r.get('outbound_date', '')),
            ('用途', r.get('purpose', '') or ''),
            ('剩余额度', f"{r.get('remaining_quota', 0):.1f} {r.get('unit', '')}"),
            ('申请占用额度', f"{r.get('requested_amount', 0):.1f} {r.get('unit', '')}"),
            ('额度缺口', f"{r.get('quota_shortage', 0):.1f} {r.get('unit', '')}"),
        ]
        for i, (label, value) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2
            tk.Label(info_frame, text=f"{label}：",
                     font=('Microsoft YaHei', 10),
                     bg='white', fg='#8c8c8c').grid(row=row, column=col, sticky='e',
                                                     padx=(0, 4), pady=4)
            tk.Label(info_frame, text=str(value),
                     font=('Microsoft YaHei', 10),
                     bg='white', fg='#262626').grid(row=row, column=col + 1, sticky='w',
                                                    padx=(0, 20), pady=4)

        if r.get('remark'):
            ttk.Separator(card, orient='horizontal').pack(fill='x', padx=20, pady=10)
            tk.Label(card, text='申请备注：',
                     font=('Microsoft YaHei', 10),
                     bg='white', fg='#8c8c8c').pack(anchor='w', padx=20)
            tk.Label(card, text=r.get('remark', ''),
                     font=('Microsoft YaHei', 10),
                     bg='white', fg='#262626',
                     wraplength=500, justify='left').pack(anchor='w', padx=20, pady=(2, 0))

        if st != 'pending':
            ttk.Separator(card, orient='horizontal').pack(fill='x', padx=20, pady=10)
            tk.Label(card, text=f"审批人：{r.get('approved_by', '')}    审批时间：{r.get('approved_at', '')}",
                     font=('Microsoft YaHei', 10),
                     bg='white', fg='#8c8c8c').pack(anchor='w', padx=20)
            if r.get('approval_note'):
                tk.Label(card, text='审批意见：',
                         font=('Microsoft YaHei', 10),
                         bg='white', fg='#8c8c8c').pack(anchor='w', padx=20, pady=(6, 0))
                tk.Label(card, text=r.get('approval_note', ''),
                         font=('Microsoft YaHei', 10),
                         bg='white', fg='#262626',
                         wraplength=500, justify='left').pack(anchor='w', padx=20, pady=(2, 0))

        btn_frame = tk.Frame(card, bg='white')
        btn_frame.pack(fill='x', pady=16, padx=20)
        tk.Button(btn_frame, text='关闭',
                  font=('Microsoft YaHei', 10),
                  relief='flat', padx=24, pady=6, cursor='hand2',
                  command=self.destroy).pack(side='right')


class ApprovalActionDialog(tk.Toplevel):
    def __init__(self, parent, approval=None, action='approve', on_success=None):
        super().__init__(parent)
        self.parent = parent
        self.approval = approval
        self.action = action
        self.on_success = on_success
        self.title('通过审批' if action == 'approve' else '拒绝审批')
        self.geometry('500x420')
        self.configure(bg='#f0f2f5')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.note_text = None
        self.approver_var = tk.StringVar()

        self._create_widgets()

    def _create_widgets(self):
        card = tk.Frame(self, bg='white')
        card.pack(fill='both', expand=True, padx=16, pady=16)

        r = self.approval or {}

        action_label = '通过' if self.action == 'approve' else '拒绝'
        action_color = '#389e0d' if self.action == 'approve' else '#cf1322'

        tk.Label(card, text=f'{action_label}出库审批',
                 font=('Microsoft YaHei', 15, 'bold'),
                 bg='white', fg=action_color).pack(anchor='w', padx=20, pady=(16, 8))

        summary = (
            f"试剂：{r.get('reagent_name', '')}    批号：{r.get('batch_no', '')}\n"
            f"数量：{r.get('quantity', 0)} {r.get('unit', '')}    "
            f"项目组：{r.get('project_name', '')}\n"
            f"申请占用：{r.get('requested_amount', 0):.1f} {r.get('unit', '')}    "
            f"剩余额度：{r.get('remaining_quota', 0):.1f} {r.get('unit', '')}    "
            f"缺口：{r.get('quota_shortage', 0):.1f} {r.get('unit', '')}"
        )
        tk.Label(card, text=summary,
                 font=('Microsoft YaHei', 10),
                 bg='white', fg='#262626',
                 justify='left').pack(anchor='w', padx=20)

        if self.action == 'approve':
            warn_text = '⚠️ 通过后将立即扣减批次库存并占用项目组额度，此操作不可撤销。'
            warn_fg = '#d48806'
        else:
            warn_text = 'ℹ️ 拒绝后将不扣库存和额度，审批记录将保留留痕。'
            warn_fg = '#8c8c8c'

        tk.Label(card, text=warn_text,
                 font=('Microsoft YaHei', 9),
                 bg='white', fg=warn_fg).pack(anchor='w', padx=20, pady=(10, 10))

        ttk.Separator(card, orient='horizontal').pack(fill='x', padx=20)

        form = tk.Frame(card, bg='white')
        form.pack(fill='x', padx=20, pady=12)

        tk.Label(form, text='审批人：',
                 font=('Microsoft YaHei', 10),
                 bg='white', fg='#595959').grid(row=0, column=0, sticky='e', padx=(0, 8), pady=6)
        tk.Entry(form, textvariable=self.approver_var,
                 font=('Microsoft YaHei', 10), width=30).grid(row=0, column=1, sticky='w', pady=6)

        tk.Label(form, text='审批意见：',
                 font=('Microsoft YaHei', 10),
                 bg='white', fg='#595959').grid(row=1, column=0, sticky='ne', padx=(0, 8), pady=6)
        self.note_text = tk.Text(form, font=('Microsoft YaHei', 10), width=38, height=6,
                                  relief='solid', bd=1)
        self.note_text.grid(row=1, column=1, sticky='w', pady=6)

        btn_frame = tk.Frame(card, bg='white')
        btn_frame.pack(fill='x', pady=8, padx=20)

        tk.Button(btn_frame, text='取消',
                  font=('Microsoft YaHei', 10),
                  relief='flat', padx=20, pady=6, cursor='hand2',
                  command=self.destroy).pack(side='right', padx=(8, 0))

        if self.action == 'approve':
            bg, abg = '#52c41a', '#73d13d'
            btn_text = '确认通过'
        else:
            bg, abg = '#ff4d4f', '#ff7875'
            btn_text = '确认拒绝'

        tk.Button(btn_frame, text=btn_text,
                  font=('Microsoft YaHei', 10),
                  bg=bg, fg='white',
                  activebackground=abg, activeforeground='white',
                  relief='flat', padx=20, pady=6, cursor='hand2',
                  command=self._on_submit).pack(side='right')

    def _on_submit(self):
        approver = self.approver_var.get().strip()
        if not approver:
            messagebox.showerror('错误', '请输入审批人', parent=self)
            return

        note = self.note_text.get('1.0', 'end').strip() or None

        try:
            if self.action == 'approve':
                outbound_db.approve_outbound(self.approval['id'], approver, note)
                messagebox.showinfo('成功', '审批已通过，库存和额度已扣减', parent=self)
            else:
                outbound_db.reject_outbound(self.approval['id'], approver, note)
                messagebox.showinfo('成功', '审批已拒绝，已记录留痕', parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror('错误', str(e), parent=self)
