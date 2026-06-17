import tkinter as tk
from tkinter import ttk, messagebox
from database import level as level_db


class LevelPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style='Content.TFrame')
        self.parent = parent
        self.levels = []
        self.projects = []
        self.current_tab = 'projects'

        self._create_widgets()
        self.refresh()

    def _create_widgets(self):
        self._create_stats_card()

        card = tk.Frame(self, bg='white')
        card.pack(fill='both', expand=True, pady=(12, 0))

        tab_bar = tk.Frame(card, bg='white')
        tab_bar.pack(fill='x', padx=16, pady=(12, 0))

        self.project_tab = tk.Label(tab_bar, text='项目组管理',
                                     font=('Microsoft YaHei', 11, 'bold'),
                                     bg='white', fg='#1890ff',
                                     padx=16, pady=10, cursor='hand2')
        self.project_tab.pack(side='left')
        self.project_tab.bind('<Button-1>', lambda e: self._switch_tab('projects'))

        self.level_tab = tk.Label(tab_bar, text='等级设置',
                                  font=('Microsoft YaHei', 11),
                                  bg='white', fg='#666',
                                  padx=16, pady=10, cursor='hand2')
        self.level_tab.pack(side='left')
        self.level_tab.bind('<Button-1>', lambda e: self._switch_tab('levels'))

        ttk.Separator(card, orient='horizontal').pack(fill='x', pady=(0, 12))

        self.project_content = tk.Frame(card, bg='white')
        self.level_content = tk.Frame(card, bg='white')

        self._create_project_tab()
        self._create_level_tab()

        self.project_content.pack(fill='both', expand=True, padx=16, pady=(0, 12))

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
        tk.Label(stats_frame.winfo_children()[0], text='项目组总数',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_quota = tk.Label(stats_frame.winfo_children()[1], text='¥0',
                                   font=('Microsoft YaHei', 18, 'bold'),
                                   bg='white', fg='#1890ff')
        self.stat_quota.pack()
        tk.Label(stats_frame.winfo_children()[1], text='总普通额度',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_used = tk.Label(stats_frame.winfo_children()[2], text='¥0',
                                  font=('Microsoft YaHei', 18, 'bold'),
                                  bg='white', fg='#fa8c16')
        self.stat_used.pack()
        tk.Label(stats_frame.winfo_children()[2], text='已使用额度',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

        self.stat_hazard = tk.Label(stats_frame.winfo_children()[3], text='¥0',
                                    font=('Microsoft YaHei', 18, 'bold'),
                                    bg='white', fg='#f5222d')
        self.stat_hazard.pack()
        tk.Label(stats_frame.winfo_children()[3], text='危化品总额度',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack()

    def _create_project_tab(self):
        header = tk.Frame(self.project_content, bg='white')
        header.pack(fill='x')

        tk.Label(header, text='项目组列表',
                 font=('Microsoft YaHei', 12, 'bold'),
                 bg='white', fg='#333').pack(side='left')

        tk.Button(header, text='+ 新增项目组',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=16, pady=6, cursor='hand2',
                  command=self._on_add_project).pack(side='right')

        table_frame = tk.Frame(self.project_content, bg='white')
        table_frame.pack(fill='both', expand=True, pady=(12, 0))

        columns = ['group_name', 'level_name', 'quota_usage', 'hazard_usage',
                   'leader', 'contact', 'action']
        self.project_tree = ttk.Treeview(table_frame, columns=columns,
                                          show='headings', height=12)

        self.project_tree.heading('group_name', text='项目组名称')
        self.project_tree.heading('level_name', text='等级')
        self.project_tree.heading('quota_usage', text='普通额度使用')
        self.project_tree.heading('hazard_usage', text='危化品额度使用')
        self.project_tree.heading('leader', text='负责人')
        self.project_tree.heading('contact', text='联系电话')
        self.project_tree.heading('action', text='操作')

        self.project_tree.column('group_name', width=160, anchor='w')
        self.project_tree.column('level_name', width=80, anchor='center')
        self.project_tree.column('quota_usage', width=200, anchor='w')
        self.project_tree.column('hazard_usage', width=180, anchor='w')
        self.project_tree.column('leader', width=90, anchor='w')
        self.project_tree.column('contact', width=120, anchor='w')
        self.project_tree.column('action', width=150, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient='vertical',
                            command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=vsb.set)

        self.project_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.project_tree.tag_configure('warning', foreground='#fa8c16')

    def _create_level_tab(self):
        header = tk.Frame(self.level_content, bg='white')
        header.pack(fill='x')

        tk.Label(header, text='等级列表',
                 font=('Microsoft YaHei', 12, 'bold'),
                 bg='white', fg='#333').pack(side='left')

        tk.Button(header, text='+ 新增等级',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=16, pady=6, cursor='hand2',
                  command=self._on_add_level).pack(side='right')

        table_frame = tk.Frame(self.level_content, bg='white')
        table_frame.pack(fill='both', expand=True, pady=(12, 0))

        columns = ['level_name', 'level_rank', 'monthly_quota',
                   'hazardous_quota', 'description', 'action']
        self.level_tree = ttk.Treeview(table_frame, columns=columns,
                                        show='headings', height=12)

        self.level_tree.heading('level_name', text='等级名称')
        self.level_tree.heading('level_rank', text='级别')
        self.level_tree.heading('monthly_quota', text='月度普通额度')
        self.level_tree.heading('hazardous_quota', text='危化品额度')
        self.level_tree.heading('description', text='说明')
        self.level_tree.heading('action', text='操作')

        self.level_tree.column('level_name', width=120, anchor='w')
        self.level_tree.column('level_rank', width=80, anchor='center')
        self.level_tree.column('monthly_quota', width=140, anchor='e')
        self.level_tree.column('hazardous_quota', width=120, anchor='e')
        self.level_tree.column('description', width=200, anchor='w')
        self.level_tree.column('action', width=120, anchor='center')

        vsb = ttk.Scrollbar(table_frame, orient='vertical',
                            command=self.level_tree.yview)
        self.level_tree.configure(yscrollcommand=vsb.set)

        self.level_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

    def _switch_tab(self, tab):
        self.current_tab = tab

        if tab == 'projects':
            self.project_tab.config(font=('Microsoft YaHei', 11, 'bold'), fg='#1890ff')
            self.level_tab.config(font=('Microsoft YaHei', 11), fg='#666')
            self.level_content.pack_forget()
            self.project_content.pack(fill='both', expand=True, padx=16, pady=(0, 12))
        else:
            self.level_tab.config(font=('Microsoft YaHei', 11, 'bold'), fg='#1890ff')
            self.project_tab.config(font=('Microsoft YaHei', 11), fg='#666')
            self.project_content.pack_forget()
            self.level_content.pack(fill='both', expand=True, padx=16, pady=(0, 12))

    def refresh(self):
        self.levels = level_db.list_levels()
        self.projects = level_db.list_projects()

        for item in self.project_tree.get_children():
            self.project_tree.delete(item)

        for item in self.level_tree.get_children():
            self.level_tree.delete(item)

        for p in self.projects:
            quota_percent = (p['used_quota'] / p['current_quota'] * 100) if p['current_quota'] > 0 else 0
            hazard_percent = (p['used_hazardous_quota'] / p['current_hazardous_quota'] * 100) if p['current_hazardous_quota'] > 0 else 0

            quota_text = f"已用 ¥{p['used_quota']:,.0f} / ¥{p['current_quota']:,.0f} ({quota_percent:.1f}%)"
            hazard_text = f"已用 ¥{p['used_hazardous_quota']:,.0f} / ¥{p['current_hazardous_quota']:,.0f} ({hazard_percent:.1f}%)"

            tags = ()
            if quota_percent > 80 or hazard_percent > 80:
                tags = ('warning',)

            self.project_tree.insert('', 'end', values=(
                p['group_name'],
                p['level_name'],
                quota_text,
                hazard_text,
                p.get('leader') or '-',
                p.get('contact') or '-',
                '详情  编辑  升降级'
            ), tags=tags)

        for l in self.levels:
            self.level_tree.insert('', 'end', values=(
                l['level_name'],
                f'第 {l["level_rank"]} 级',
                f"¥{l['monthly_quota']:,.0f}",
                f"¥{l['hazardous_quota']:,.0f}",
                l.get('description') or '-',
                '编辑  删除'
            ))

        total_quota = sum(p['current_quota'] for p in self.projects)
        total_used = sum(p['used_quota'] for p in self.projects)
        total_hazardous = sum(p['current_hazardous_quota'] for p in self.projects)

        self.stat_total.config(text=str(len(self.projects)))
        self.stat_quota.config(text=f"¥{total_quota:,.0f}")
        self.stat_used.config(text=f"¥{total_used:,.0f}")
        self.stat_hazard.config(text=f"¥{total_hazardous:,.0f}")

    def _on_add_project(self):
        ProjectDialog(self, levels=self.levels, mode='add', on_success=self.refresh)

    def _on_add_level(self):
        LevelDialog(self, mode='add', on_success=self.refresh)


class LevelDialog(tk.Toplevel):
    def __init__(self, parent, mode='add', data=None, on_success=None):
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        self.data = data
        self.on_success = on_success

        self.title('新增等级' if mode == 'add' else '编辑等级')
        self.geometry('440x380')
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
        row1.pack(fill='x', pady=8)
        self._add_field(row1, 'level_name', '等级名称 *', 20)
        self._add_field(row1, 'level_rank', '级别排序 *', 20)

        row2 = tk.Frame(form, bg='white')
        row2.pack(fill='x', pady=8)
        self._add_field(row2, 'monthly_quota', '月度普通额度 *', 20)
        self._add_field(row2, 'hazardous_quota', '危化品额度 *', 20)

        tk.Label(form, text='说明', font=('Microsoft YaHei', 10),
                 bg='white', fg='#333').pack(anchor='w', pady=(8, 0))
        self.entries['description'] = tk.Text(form, height=3,
                                               font=('Microsoft YaHei', 10))
        self.entries['description'].pack(fill='x', pady=(4, 0))

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
        self.entries['level_name'].insert(0, data.get('level_name', ''))
        self.entries['level_rank'].insert(0, str(data.get('level_rank', '')))
        self.entries['monthly_quota'].insert(0, str(data.get('monthly_quota', '')))
        self.entries['hazardous_quota'].insert(0, str(data.get('hazardous_quota', '')))
        self.entries['description'].insert('1.0', data.get('description', ''))

    def _on_submit(self):
        data = {
            'level_name': self.entries['level_name'].get().strip(),
            'level_rank': int(self.entries['level_rank'].get() or 0),
            'monthly_quota': float(self.entries['monthly_quota'].get() or 0),
            'hazardous_quota': float(self.entries['hazardous_quota'].get() or 0),
            'description': self.entries['description'].get('1.0', 'end').strip() or None
        }

        if not data['level_name']:
            messagebox.showerror('错误', '请输入等级名称', parent=self)
            return
        if data['level_rank'] <= 0:
            messagebox.showerror('错误', '级别必须大于0', parent=self)
            return

        try:
            if self.mode == 'add':
                level_db.create_level(data)
                messagebox.showinfo('成功', '新增成功', parent=self)
            else:
                level_db.update_level(self.data['id'], data)
                messagebox.showinfo('成功', '修改成功', parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror('错误', str(e), parent=self)


class ProjectDialog(tk.Toplevel):
    def __init__(self, parent, levels=None, mode='add', data=None, on_success=None):
        super().__init__(parent)
        self.parent = parent
        self.levels = levels or []
        self.mode = mode
        self.data = data
        self.on_success = on_success

        self.title('新增项目组' if mode == 'add' else '编辑项目组')
        self.geometry('440x360')
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

        self._add_field(form, 'group_name', '项目组名称 *')

        tk.Label(form, text='所属等级 *', font=('Microsoft YaHei', 10),
                 bg='white', fg='#333').pack(anchor='w', pady=(8, 0))
        self.level_var = tk.StringVar()
        self.level_combo = ttk.Combobox(form, textvariable=self.level_var,
                                        state='readonly',
                                        values=[l['level_name'] for l in self.levels])
        self.level_combo.pack(fill='x', pady=(4, 0))

        row1 = tk.Frame(form, bg='white')
        row1.pack(fill='x', pady=8)
        self._add_field(row1, 'leader', '负责人', 20)
        self._add_field(row1, 'contact', '联系电话', 20)

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
        field_frame.pack(fill='x', pady=4)
        tk.Label(field_frame, text=label, font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack(anchor='w')
        entry = tk.Entry(field_frame, font=('Microsoft YaHei', 10))
        entry.pack(fill='x', pady=(4, 0))
        self.entries[name] = entry

    def _fill_data(self, data):
        self.entries['group_name'].insert(0, data.get('group_name', ''))
        self.entries['leader'].insert(0, data.get('leader') or '')
        self.entries['contact'].insert(0, data.get('contact') or '')

        for l in self.levels:
            if l['id'] == data['level_id']:
                self.level_var.set(l['level_name'])
                break

    def _on_submit(self):
        group_name = self.entries['group_name'].get().strip()
        if not group_name:
            messagebox.showerror('错误', '请输入项目组名称', parent=self)
            return

        level_id = None
        for l in self.levels:
            if l['level_name'] == self.level_var.get():
                level_id = l['id']
                break

        if not level_id:
            messagebox.showerror('错误', '请选择等级', parent=self)
            return

        data = {
            'group_name': group_name,
            'level_id': level_id,
            'leader': self.entries['leader'].get().strip() or None,
            'contact': self.entries['contact'].get().strip() or None
        }

        try:
            if self.mode == 'add':
                level_db.create_project(data)
                messagebox.showinfo('成功', '新增成功', parent=self)
            else:
                level_db.update_project(self.data['id'], data)
                messagebox.showinfo('成功', '修改成功', parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror('错误', str(e), parent=self)
