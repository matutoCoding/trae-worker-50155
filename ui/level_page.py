import tkinter as tk
from tkinter import ttk, messagebox
from database import level as level_db
import re


def _validate_positive_int(value, field_name):
    value = value.strip()
    if not value:
        raise ValueError(f'{field_name}不能为空')
    if re.search(r'[^\d]', value):
        raise ValueError(f'{field_name}只能输入正整数，请不要输入中文、空格或特殊字符')
    num = int(value)
    if num <= 0:
        raise ValueError(f'{field_name}必须大于0')
    return num


def _validate_positive_float(value, field_name):
    value = value.strip()
    if not value:
        raise ValueError(f'{field_name}不能为空')
    if re.search(r'[^\d.]', value) or value.count('.') > 1 or value.startswith('.') or value.endswith('.'):
        raise ValueError(f'{field_name}只能输入正数，请不要输入中文、空格或特殊字符')
    num = float(value)
    if num <= 0:
        raise ValueError(f'{field_name}必须大于0')
    return num


def _validate_nonneg_float(value, field_name):
    value = value.strip()
    if not value:
        return 0
    if re.search(r'[^\d.]', value) or value.count('.') > 1 or value.startswith('.') or value.endswith('.'):
        raise ValueError(f'{field_name}只能输入非负数，请不要输入中文、空格或特殊字符')
    num = float(value)
    if num < 0:
        raise ValueError(f'{field_name}不能为负数')
    return num


class LevelPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style='Content.TFrame')
        self.parent = parent
        self.levels = []
        self.projects = []
        self.current_tab = 'projects'
        self.project_data_cache = {}
        self.level_data_cache = {}

        self._create_widgets()
        self._bind_events()
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

        btn_group = tk.Frame(header, bg='white')
        btn_group.pack(side='right')

        tk.Button(btn_group, text='+ 新增项目组',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=16, pady=6, cursor='hand2',
                  command=self._on_add_project).pack(side='right', padx=(8, 0))

        tk.Button(btn_group, text='升降级',
                  font=('Microsoft YaHei', 10),
                  bg='#52c41a', fg='white',
                  activebackground='#73d13d', activeforeground='white',
                  relief='flat', padx=12, pady=6, cursor='hand2',
                  command=self._on_change_level).pack(side='right')

        tk.Button(btn_group, text='编辑',
                  font=('Microsoft YaHei', 10),
                  bg='#fa8c16', fg='white',
                  activebackground='#ffa940', activeforeground='white',
                  relief='flat', padx=12, pady=6, cursor='hand2',
                  command=self._on_edit_project).pack(side='right', padx=(0, 8))

        tk.Label(self.project_content, text='（双击行可编辑，右键可查看更多操作）',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#999').pack(anchor='w', pady=(8, 0))

        table_frame = tk.Frame(self.project_content, bg='white')
        table_frame.pack(fill='both', expand=True, pady=(8, 0))

        columns = ['group_name', 'level_name', 'quota_usage', 'hazard_usage',
                   'leader', 'contact']
        self.project_tree = ttk.Treeview(table_frame, columns=columns,
                                          show='headings', height=12)

        self.project_tree.heading('group_name', text='项目组名称')
        self.project_tree.heading('level_name', text='等级')
        self.project_tree.heading('quota_usage', text='普通额度使用')
        self.project_tree.heading('hazard_usage', text='危化品额度使用')
        self.project_tree.heading('leader', text='负责人')
        self.project_tree.heading('contact', text='联系电话')

        self.project_tree.column('group_name', width=160, anchor='w')
        self.project_tree.column('level_name', width=80, anchor='center')
        self.project_tree.column('quota_usage', width=240, anchor='w')
        self.project_tree.column('hazard_usage', width=220, anchor='w')
        self.project_tree.column('leader', width=90, anchor='w')
        self.project_tree.column('contact', width=120, anchor='w')

        vsb = ttk.Scrollbar(table_frame, orient='vertical',
                            command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=vsb.set)

        self.project_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.project_tree.tag_configure('warning', foreground='#fa8c16')

        self.project_context_menu = tk.Menu(self.project_tree, tearoff=0)
        self.project_context_menu.add_command(label='查看详情', command=self._on_project_detail)
        self.project_context_menu.add_command(label='编辑', command=self._on_edit_project)
        self.project_context_menu.add_command(label='升降级', command=self._on_change_level)
        self.project_context_menu.add_separator()
        self.project_context_menu.add_command(label='删除', command=self._on_delete_project)

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

        self.level_context_menu = tk.Menu(self.level_tree, tearoff=0)
        self.level_context_menu.add_command(label='编辑', command=self._on_edit_level)
        self.level_context_menu.add_separator()
        self.level_context_menu.add_command(label='删除', command=self._on_delete_level)

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
        self.project_data_cache.clear()

        for item in self.level_tree.get_children():
            self.level_tree.delete(item)
        self.level_data_cache.clear()

        for p in self.projects:
            quota_percent = (p['used_quota'] / p['current_quota'] * 100) if p['current_quota'] > 0 else 0
            hazard_percent = (p['used_hazardous_quota'] / p['current_hazardous_quota'] * 100) if p['current_hazardous_quota'] > 0 else 0

            quota_text = f"已用 ¥{p['used_quota']:,.0f} / ¥{p['current_quota']:,.0f} ({quota_percent:.1f}%)"
            hazard_text = f"已用 ¥{p['used_hazardous_quota']:,.0f} / ¥{p['current_hazardous_quota']:,.0f} ({hazard_percent:.1f}%)"

            tags = ()
            if quota_percent > 80 or hazard_percent > 80:
                tags = ('warning',)

            item_id = self.project_tree.insert('', 'end', values=(
                p['group_name'],
                p['level_name'],
                quota_text,
                hazard_text,
                p.get('leader') or '-',
                p.get('contact') or '-'
            ), tags=tags)

            self.project_data_cache[item_id] = p

        for l in self.levels:
            item_id = self.level_tree.insert('', 'end', values=(
                l['level_name'],
                f'第 {l["level_rank"]} 级',
                f"¥{l['monthly_quota']:,.0f}",
                f"¥{l['hazardous_quota']:,.0f}",
                l.get('description') or '-'
            ))
            self.level_data_cache[item_id] = l

        total_quota = sum(p['current_quota'] for p in self.projects)
        total_used = sum(p['used_quota'] for p in self.projects)
        total_hazardous = sum(p['current_hazardous_quota'] for p in self.projects)

        self.stat_total.config(text=str(len(self.projects)))
        self.stat_quota.config(text=f"¥{total_quota:,.0f}")
        self.stat_used.config(text=f"¥{total_used:,.0f}")
        self.stat_hazard.config(text=f"¥{total_hazardous:,.0f}")

    def _bind_events(self):
        self.project_tree.bind('<Double-1>', self._on_project_double_click)
        self.project_tree.bind('<Button-3>', self._on_project_right_click)
        self.level_tree.bind('<Double-1>', self._on_level_double_click)
        self.level_tree.bind('<Button-3>', self._on_level_right_click)

    def _get_selected_project(self):
        selection = self.project_tree.selection()
        if not selection:
            return None
        item_id = selection[0]
        return self.project_data_cache.get(item_id)

    def _get_selected_level(self):
        selection = self.level_tree.selection()
        if not selection:
            return None
        item_id = selection[0]
        return self.level_data_cache.get(item_id)

    def _on_project_double_click(self, event):
        self._on_edit_project()

    def _on_project_right_click(self, event):
        item = self.project_tree.identify_row(event.y)
        if item:
            self.project_tree.selection_set(item)
            self.project_context_menu.post(event.x_root, event.y_root)

    def _on_level_double_click(self, event):
        self._on_edit_level()

    def _on_level_right_click(self, event):
        item = self.level_tree.identify_row(event.y)
        if item:
            self.level_tree.selection_set(item)
            self.level_context_menu.post(event.x_root, event.y_root)

    def _on_add_project(self):
        ProjectDialog(self, levels=self.levels, mode='add', on_success=self.refresh)

    def _on_edit_project(self):
        project = self._get_selected_project()
        if not project:
            messagebox.showwarning('提示', '请先选择一个项目组', parent=self)
            return
        ProjectDialog(self, levels=self.levels, mode='edit', data=project, on_success=self.refresh)

    def _on_delete_project(self):
        project = self._get_selected_project()
        if not project:
            messagebox.showwarning('提示', '请先选择一个项目组', parent=self)
            return
        if messagebox.askyesno('确认删除',
                               f'确定要删除项目组 "{project["group_name"]}" 吗？\n此操作不可恢复！',
                               parent=self, icon='warning'):
            try:
                level_db.delete_project(project['id'])
                messagebox.showinfo('成功', '删除成功', parent=self)
                self.refresh()
            except Exception as e:
                messagebox.showerror('错误', str(e), parent=self)

    def _on_project_detail(self):
        project = self._get_selected_project()
        if not project:
            messagebox.showwarning('提示', '请先选择一个项目组', parent=self)
            return
        ProjectDetailDialog(self, project['id'])

    def _on_change_level(self):
        project = self._get_selected_project()
        if not project:
            messagebox.showwarning('提示', '请先选择一个项目组', parent=self)
            return
        LevelChangeDialog(self, project, self.levels, on_success=self.refresh)

    def _on_add_level(self):
        LevelDialog(self, mode='add', on_success=self.refresh)

    def _on_edit_level(self):
        level = self._get_selected_level()
        if not level:
            messagebox.showwarning('提示', '请先选择一个等级', parent=self)
            return
        LevelDialog(self, mode='edit', data=level, on_success=self.refresh)

    def _on_delete_level(self):
        level = self._get_selected_level()
        if not level:
            messagebox.showwarning('提示', '请先选择一个等级', parent=self)
            return
        if messagebox.askyesno('确认删除',
                               f'确定要删除等级 "{level["level_name"]}" 吗？\n此操作不可恢复！',
                               parent=self, icon='warning'):
            try:
                level_db.delete_level(level['id'])
                messagebox.showinfo('成功', '删除成功', parent=self)
                self.refresh()
            except Exception as e:
                messagebox.showerror('错误', str(e), parent=self)


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
            'description': self.entries['description'].get('1.0', 'end').strip() or None
        }

        if not data['level_name']:
            messagebox.showerror('错误', '请输入等级名称', parent=self)
            return

        try:
            data['level_rank'] = _validate_positive_int(
                self.entries['level_rank'].get(), '级别排序')
            data['monthly_quota'] = _validate_positive_float(
                self.entries['monthly_quota'].get(), '月度普通额度')
            data['hazardous_quota'] = _validate_nonneg_float(
                self.entries['hazardous_quota'].get(), '危化品额度')
        except ValueError as e:
            messagebox.showerror('输入错误', str(e), parent=self)
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


class LevelChangeDialog(tk.Toplevel):
    def __init__(self, parent, project, levels, on_success=None):
        super().__init__(parent)
        self.parent = parent
        self.project = project
        self.levels = levels
        self.on_success = on_success
        self.carry_over_var = tk.BooleanVar(value=True)

        self.title('项目组升降级')
        self.geometry('480x420')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()
        self._calc_preview()

    def _create_widgets(self):
        container = tk.Frame(self, bg='white')
        container.pack(fill='both', expand=True, padx=20, pady=16)

        tk.Label(container, text='项目组升降级',
                 font=('Microsoft YaHei', 14, 'bold'),
                 bg='white', fg='#333').pack(anchor='w')

        info_frame = tk.Frame(container, bg='#f0f7ff', bd=1, relief='solid')
        info_frame.pack(fill='x', pady=12)

        info_data = [
            ('项目组', self.project['group_name']),
            ('当前等级', self.project['level_name']),
            ('普通额度', f"¥{self.project['current_quota']:,.0f} (已用 ¥{self.project['used_quota']:,.0f})"),
            ('危化品额度', f"¥{self.project['current_hazardous_quota']:,.0f} (已用 ¥{self.project['used_hazardous_quota']:,.0f})"),
        ]

        for i, (label, value) in enumerate(info_data):
            row = tk.Frame(info_frame, bg='#f0f7ff')
            row.pack(fill='x', padx=12, pady=6)
            tk.Label(row, text=label + '：',
                     font=('Microsoft YaHei', 9),
                     bg='#f0f7ff', fg='#666').pack(side='left')
            tk.Label(row, text=str(value),
                     font=('Microsoft YaHei', 10),
                     bg='#f0f7ff', fg='#333').pack(side='left')

        tk.Label(container, text='选择新等级 *', font=('Microsoft YaHei', 10),
                 bg='white', fg='#333').pack(anchor='w', pady=(4, 0))
        self.new_level_var = tk.StringVar()
        level_names = [l['level_name'] for l in self.levels if l['id'] != self.project['level_id']]
        self.level_combo = ttk.Combobox(container, textvariable=self.new_level_var,
                                        state='readonly', values=level_names)
        self.level_combo.pack(fill='x', pady=(4, 12))
        self.level_combo.bind('<<ComboboxSelected>>', lambda e: self._calc_preview())

        tk.Label(container, text='结转方式', font=('Microsoft YaHei', 10),
                 bg='white', fg='#333').pack(anchor='w')

        carry_frame = tk.Frame(container, bg='white')
        carry_frame.pack(fill='x', pady=(4, 0))

        tk.Radiobutton(carry_frame, text='按比例结转剩余额度',
                       variable=self.carry_over_var, value=True,
                       bg='white', activebackground='white',
                       font=('Microsoft YaHei', 10),
                       command=self._calc_preview).pack(anchor='w', pady=2)
        tk.Label(carry_frame,
                 text='  剩余额度按原等级比例折算到新等级，累加到新等级标准额度上',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#999').pack(anchor='w', padx=(20, 0))

        tk.Radiobutton(carry_frame, text='清零重置',
                       variable=self.carry_over_var, value=False,
                       bg='white', activebackground='white',
                       font=('Microsoft YaHei', 10),
                       command=self._calc_preview).pack(anchor='w', pady=(8, 2))
        tk.Label(carry_frame,
                 text='  直接使用新等级的标准额度，已用额度清零',
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#999').pack(anchor='w', padx=(20, 0))

        self.preview_frame = tk.Frame(container, bg='#fff7e6', bd=1, relief='solid')
        self.preview_frame.pack(fill='x', pady=12)

        tk.Label(self.preview_frame, text='变更后预览',
                 font=('Microsoft YaHei', 10, 'bold'),
                 bg='#fff7e6', fg='#fa8c16').pack(anchor='w', padx=12, pady=(8, 4))

        self.preview_text = tk.Label(self.preview_frame, text='请选择新等级',
                                     font=('Microsoft YaHei', 9),
                                     bg='#fff7e6', fg='#666', justify='left')
        self.preview_text.pack(anchor='w', padx=12, pady=(0, 8))

        btn_frame = tk.Frame(self, bg='#fafafa')
        btn_frame.pack(fill='x', side='bottom')

        tk.Button(btn_frame, text='取消',
                  font=('Microsoft YaHei', 10),
                  bg='white', fg='#666',
                  activebackground='#f5f5f5',
                  relief='flat', padx=20, pady=8, cursor='hand2',
                  command=self.destroy).pack(side='right', padx=12, pady=12)

        tk.Button(btn_frame, text='确认变更',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=20, pady=8, cursor='hand2',
                  command=self._on_submit).pack(side='right', pady=12)

    def _calc_preview(self):
        new_level_name = self.new_level_var.get()
        if not new_level_name:
            self.preview_text.config(text='请选择新等级')
            return

        new_level = None
        for l in self.levels:
            if l['level_name'] == new_level_name:
                new_level = l
                break

        if not new_level:
            return

        carry_over = self.carry_over_var.get()
        remaining_quota = self.project['current_quota'] - self.project['used_quota']
        remaining_hazardous = self.project['current_hazardous_quota'] - self.project['used_hazardous_quota']

        new_quota = new_level['monthly_quota']
        new_hazardous = new_level['hazardous_quota']
        carry_over_amount = 0
        carry_over_hazardous = 0

        if carry_over:
            old_monthly = self.project.get('monthly_quota', self.project['current_quota'])
            old_hazardous_quota = self.project.get('hazardous_quota', self.project['current_hazardous_quota'])
            
            if old_monthly > 0 and remaining_quota > 0:
                ratio = remaining_quota / old_monthly
                carry_over_amount = min(remaining_quota, new_level['monthly_quota'] * ratio)
                new_quota = new_level['monthly_quota'] + carry_over_amount

            if old_hazardous_quota > 0 and remaining_hazardous > 0:
                hazard_ratio = remaining_hazardous / old_hazardous_quota
                carry_over_hazardous = min(remaining_hazardous, new_level['hazardous_quota'] * hazard_ratio)
                new_hazardous = new_level['hazardous_quota'] + carry_over_hazardous

        normal_preview = f"• 普通额度：¥{new_quota:,.0f} (标准 ¥{new_level['monthly_quota']:,.0f}"
        if carry_over and carry_over_amount > 0:
            normal_preview += f", 结转 ¥{carry_over_amount:,.0f}"
        normal_preview += ")"

        hazard_preview = f"• 危化品额度：¥{new_hazardous:,.0f} (标准 ¥{new_level['hazardous_quota']:,.0f}"
        if carry_over and carry_over_hazardous > 0:
            hazard_preview += f", 结转 ¥{carry_over_hazardous:,.0f}"
        hazard_preview += ")"

        preview = (f"• 新等级：{new_level_name}\n"
                   f"{normal_preview}\n"
                   f"{hazard_preview}\n"
                   f"• 已用额度清零重算")

        self.preview_text.config(text=preview)

    def _on_submit(self):
        new_level_name = self.new_level_var.get()
        if not new_level_name:
            messagebox.showerror('错误', '请选择新等级', parent=self)
            return

        new_level_id = None
        for l in self.levels:
            if l['level_name'] == new_level_name:
                new_level_id = l['id']
                break

        if not new_level_id:
            messagebox.showerror('错误', '无效的等级', parent=self)
            return

        carry_over = self.carry_over_var.get()
        carry_text = '按比例结转' if carry_over else '清零重置'

        if not messagebox.askyesno('确认变更',
                                   f'确定要将 "{self.project["group_name"]}" '
                                   f'从 {self.project["level_name"]} 变更为 {new_level_name} 吗？\n'
                                   f'结转方式：{carry_text}',
                                   parent=self, icon='question'):
            return

        try:
            level_db.change_project_level(self.project['id'], new_level_id, carry_over)
            messagebox.showinfo('成功', '升降级操作成功', parent=self)
            if self.on_success:
                self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror('错误', str(e), parent=self)


class ProjectDetailDialog(tk.Toplevel):
    def __init__(self, parent, project_id):
        super().__init__(parent)
        self.parent = parent
        self.project_id = project_id

        self.title('项目组详情')
        self.geometry('620x540')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        container = tk.Frame(self, bg='white')
        container.pack(fill='both', expand=True, padx=20, pady=16)

        projects = level_db.list_projects()
        self.project = None
        for p in projects:
            if p['id'] == self.project_id:
                self.project = p
                break
        if not self.project:
            tk.Label(container, text='项目组不存在', font=('Microsoft YaHei', 12),
                     bg='white', fg='#f5222d').pack()
            return

        tk.Label(container, text=self.project['group_name'],
                 font=('Microsoft YaHei', 14, 'bold'),
                 bg='white', fg='#333').pack(anchor='w')

        tk.Label(container, text=f"等级：{self.project['level_name']}",
                 font=('Microsoft YaHei', 10),
                 bg='white', fg='#1890ff').pack(anchor='w', pady=(4, 12))

        info_frame = tk.Frame(container, bg='#fafafa', bd=1, relief='solid')
        info_frame.pack(fill='x')

        info_data = [
            ('负责人', self.project.get('leader') or '-'),
            ('联系电话', self.project.get('contact') or '-'),
            ('额度月份', self.project.get('quota_month') or '-'),
        ]

        for i, (label, value) in enumerate(info_data):
            row = tk.Frame(info_frame, bg='#fafafa')
            row.pack(fill='x', padx=12, pady=6)
            tk.Label(row, text=label + '：',
                     font=('Microsoft YaHei', 9),
                     bg='#fafafa', fg='#666').pack(side='left')
            tk.Label(row, text=str(value),
                     font=('Microsoft YaHei', 10),
                     bg='#fafafa', fg='#333').pack(side='left')

        quota_frame = tk.Frame(container, bg='white')
        quota_frame.pack(fill='x', pady=16)

        tk.Label(quota_frame, text='额度使用情况',
                 font=('Microsoft YaHei', 11, 'bold'),
                 bg='white', fg='#333').pack(anchor='w')

        normal_frame = tk.Frame(quota_frame, bg='white')
        normal_frame.pack(fill='x', pady=(8, 4))

        normal_percent = (self.project['used_quota'] / self.project['current_quota'] * 100) if self.project['current_quota'] > 0 else 0
        tk.Label(normal_frame, text=f"普通额度：已用 ¥{self.project['used_quota']:,.0f} / ¥{self.project['current_quota']:,.0f}",
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack(anchor='w')

        bar_bg = tk.Frame(quota_frame, bg='#f0f0f0', height=16)
        bar_bg.pack(fill='x', pady=(0, 4))
        bar_width = max(1, int(normal_percent * 4.8))
        bar_color = '#52c41a' if normal_percent < 60 else '#fa8c16' if normal_percent < 80 else '#f5222d'
        tk.Frame(bar_bg, bg=bar_color, width=bar_width, height=16).pack(side='left')

        hazard_frame = tk.Frame(quota_frame, bg='white')
        hazard_frame.pack(fill='x', pady=(12, 4))

        hazard_percent = (self.project['used_hazardous_quota'] / self.project['current_hazardous_quota'] * 100) if self.project['current_hazardous_quota'] > 0 else 0
        tk.Label(hazard_frame, text=f"危化品额度：已用 ¥{self.project['used_hazardous_quota']:,.0f} / ¥{self.project['current_hazardous_quota']:,.0f}",
                 font=('Microsoft YaHei', 9),
                 bg='white', fg='#666').pack(anchor='w')

        bar_bg2 = tk.Frame(quota_frame, bg='#f0f0f0', height=16)
        bar_bg2.pack(fill='x', pady=(0, 4))
        bar_width2 = max(1, int(hazard_percent * 4.8))
        bar_color2 = '#52c41a' if hazard_percent < 60 else '#fa8c16' if hazard_percent < 80 else '#f5222d'
        tk.Frame(bar_bg2, bg=bar_color2, width=bar_width2, height=16).pack(side='left')

        tk.Label(container, text='升降级记录',
                 font=('Microsoft YaHei', 11, 'bold'),
                 bg='white', fg='#333').pack(anchor='w', pady=(12, 8))

        try:
            result = level_db.get_quota_usage(self.project['id'])
            change_logs = result['change_logs']
        except:
            change_logs = []

        logs_frame = tk.Frame(container, bg='white')
        logs_frame.pack(fill='both', expand=True)

        columns = ['date', 'old_level', 'new_level', 'type', 'quota_change']
        log_tree = ttk.Treeview(logs_frame, columns=columns, show='headings', height=6)

        log_tree.heading('date', text='时间')
        log_tree.heading('old_level', text='原等级')
        log_tree.heading('new_level', text='新等级')
        log_tree.heading('type', text='结转方式')
        log_tree.heading('quota_change', text='额度变化')

        log_tree.column('date', width=130, anchor='w')
        log_tree.column('old_level', width=70, anchor='center')
        log_tree.column('new_level', width=70, anchor='center')
        log_tree.column('type', width=80, anchor='center')
        log_tree.column('quota_change', width=200, anchor='w')

        vsb = ttk.Scrollbar(logs_frame, orient='vertical', command=log_tree.yview)
        log_tree.configure(yscrollcommand=vsb.set)

        log_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        for log in change_logs:
            type_text = '按比例结转' if log['carry_over_type'] == 'proportional' else '清零重置'
            parts = []
            old_q = log.get('old_quota')
            new_q = log.get('new_quota')
            if old_q is not None and new_q is not None:
                diff = new_q - old_q
                sign = '+' if diff >= 0 else ''
                parts.append(f"普通 ¥{old_q:,.0f}→¥{new_q:,.0f}({sign}¥{diff:,.0f})")
            old_hq = log.get('old_hazardous_quota')
            new_hq = log.get('new_hazardous_quota')
            if old_hq is not None and new_hq is not None:
                hdiff = new_hq - old_hq
                hsign = '+' if hdiff >= 0 else ''
                parts.append(f"危化 ¥{old_hq:,.0f}→¥{new_hq:,.0f}({hsign}¥{hdiff:,.0f})")
            quota_text = '；'.join(parts) if parts else (log.get('remark') or '')
            log_tree.insert('', 'end', values=(
                log.get('created_at', ''),
                log.get('old_level_name') or '-',
                log.get('new_level_name') or '-',
                type_text,
                quota_text
            ))

        btn_frame = tk.Frame(self, bg='#fafafa')
        btn_frame.pack(fill='x', side='bottom')

        tk.Button(btn_frame, text='关闭',
                  font=('Microsoft YaHei', 10),
                  bg='#1890ff', fg='white',
                  activebackground='#40a9ff', activeforeground='white',
                  relief='flat', padx=24, pady=8, cursor='hand2',
                  command=self.destroy).pack(side='right', padx=12, pady=12)
