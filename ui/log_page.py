import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from database import log as log_db
from database import qualification as qual_db
from database import level as level_db


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

        self.projects = []

        self._create_widgets()
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

        ttk.Separator(card, orient='horizontal').pack(fill='x', pady=(0, 12))

        self.operation_content = tk.Frame(card, bg='white')
        self.qualification_content = tk.Frame(card, bg='white')

        self._create_operation_tab()
        self._create_qualification_tab()

        self.operation_content.pack(fill='both', expand=True, padx=16, pady=(0, 12))

    def _create_stats_card(self):
        stats_frame = tk.Frame(self, bg='white')
        stats_frame.pack(fill='x')

        for i in range(4):
            col = tk.Frame(stats_frame, bg='white')
            col.pack(side='left', fill='x', expand=True, padx=8, pady=12)

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
        tk.Label(stats_frame.winfo_children()[2], text='即将过期',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_expired = tk.Label(stats_frame.winfo_children()[3], text='0',
                                     font=('Microsoft YaHei', 18, 'bold'),
                                     bg='white', fg='#f5222d')
        self.stat_expired.pack()
        tk.Label(stats_frame.winfo_children()[3], text='已过期',
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

        tk.Button(header, text='+ 新增资质',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=16, pady=6, cursor='hand2',
                  command=self._on_add_qual).pack(side='right')

        search_bar = tk.Frame(self.qualification_content, bg='white')
        search_bar.pack(fill='x', pady=12)

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
                   'expiry', 'status', 'action']
        self.qual_tree = ttk.Treeview(table_frame, columns=columns,
                                       show='headings', height=12)

        self.qual_tree.heading('qual_type', text='资质类型')
        self.qual_tree.heading('cert_no', text='证书编号')
        self.qual_tree.heading('holder', text='持有人')
        self.qual_tree.heading('project', text='所属项目')
        self.qual_tree.heading('expiry', text='有效期')
        self.qual_tree.heading('status', text='状态')
        self.qual_tree.heading('action', text='操作')

        self.qual_tree.column('qual_type', width=150, anchor='w')
        self.qual_tree.column('cert_no', width=150, anchor='w')
        self.qual_tree.column('holder', width=100, anchor='w')
        self.qual_tree.column('project', width=130, anchor='w')
        self.qual_tree.column('expiry', width=130, anchor='center')
        self.qual_tree.column('status', width=80, anchor='center')
        self.qual_tree.column('action', width=120, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient='vertical',
                            command=self.qual_tree.yview)
        self.qual_tree.configure(yscrollcommand=vsb.set)

        self.qual_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.qual_tree.tag_configure('expired', foreground='#f5222d')
        self.qual_tree.tag_configure('warning', foreground='#fa8c16')

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

        if tab == 'operation':
            self.op_tab.config(font=('Microsoft YaHei', 11, 'bold'), fg='#1890ff')
            self.qual_tab.config(font=('Microsoft YaHei', 11), fg='#666')
            self.qualification_content.pack_forget()
            self.operation_content.pack(fill='both', expand=True, padx=16, pady=(0, 12))
        else:
            self.qual_tab.config(font=('Microsoft YaHei', 11, 'bold'), fg='#1890ff')
            self.op_tab.config(font=('Microsoft YaHei', 11), fg='#666')
            self.operation_content.pack_forget()
            self.qualification_content.pack(fill='both', expand=True, padx=16, pady=(0, 12))

    def refresh(self):
        self._load_logs()
        self._load_quals()
        self.projects = level_db.list_projects()

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

            self.qual_tree.insert('', 'end', values=(
                row['qualification_type'],
                row['certificate_no'],
                row.get('holder_name') or '-',
                row.get('project_name') or '-',
                expiry_text,
                status_text,
                '编辑  删除'
            ), tags=tags)

        self.qual_page_info.config(text=f'共 {self.qual_total} 条记录')
        self.qual_page_label.config(text=f'第 {self.qual_page} 页')

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
