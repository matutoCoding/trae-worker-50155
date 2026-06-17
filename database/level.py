from database.db import get_conn, add_operation_log


def list_levels():
    """获取所有等级列表"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM project_levels ORDER BY level_rank ASC')
    return [dict(row) for row in cursor.fetchall()]


def get_level(level_id):
    """获取单个等级"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM project_levels WHERE id = ?', (level_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def create_level(data):
    """新增等级"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO project_levels (level_name, level_rank, monthly_quota, hazardous_quota, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data['level_name'],
        data['level_rank'],
        data.get('monthly_quota', 0),
        data.get('hazardous_quota', 0),
        data.get('description')
    ))

    conn.commit()
    level_id = cursor.lastrowid

    add_operation_log('等级额度', '新增', f'新增等级: {data["level_name"]}')

    return level_id


def update_level(level_id, data):
    """更新等级"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE project_levels SET
            level_name = ?, level_rank = ?, monthly_quota = ?,
            hazardous_quota = ?, description = ?
        WHERE id = ?
    ''', (
        data['level_name'],
        data['level_rank'],
        data.get('monthly_quota', 0),
        data.get('hazardous_quota', 0),
        data.get('description'),
        level_id
    ))

    conn.commit()
    add_operation_log('等级额度', '修改', f'修改等级: {data["level_name"]}')

    return cursor.rowcount


def delete_level(level_id):
    """删除等级"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('SELECT level_name FROM project_levels WHERE id = ?', (level_id,))
    level = cursor.fetchone()

    cursor.execute('DELETE FROM project_levels WHERE id = ?', (level_id,))
    conn.commit()

    if level:
        add_operation_log('等级额度', '删除', f'删除等级: {level["level_name"]}')

    return cursor.rowcount


def list_projects():
    """获取所有项目组列表"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, l.level_name, l.level_rank, l.monthly_quota, l.hazardous_quota
        FROM project_groups p
        LEFT JOIN project_levels l ON p.level_id = l.id
        ORDER BY l.level_rank ASC, p.group_name ASC
    ''')
    return [dict(row) for row in cursor.fetchall()]


def create_project(data):
    """新增项目组"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM project_levels WHERE id = ?', (data['level_id'],))
    level = cursor.fetchone()
    if not level:
        raise Exception('等级不存在')

    cursor.execute('''
        INSERT INTO project_groups (
            group_name, level_id, current_quota, current_hazardous_quota,
            quota_month, leader, contact
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['group_name'],
        data['level_id'],
        level['monthly_quota'],
        level['hazardous_quota'],
        data.get('quota_month'),
        data.get('leader'),
        data.get('contact')
    ))

    conn.commit()
    project_id = cursor.lastrowid

    add_operation_log('等级额度', '新增项目组', f'新增项目组: {data["group_name"]}')

    return project_id


def update_project(project_id, data):
    """更新项目组"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE project_groups SET
            group_name = ?, leader = ?, contact = ?,
            updated_at = datetime('now','localtime')
        WHERE id = ?
    ''', (
        data['group_name'],
        data.get('leader'),
        data.get('contact'),
        project_id
    ))

    conn.commit()
    add_operation_log('等级额度', '修改项目组', f'修改项目组: {data["group_name"]}')

    return cursor.rowcount


def change_project_level(project_id, new_level_id, carry_over):
    """项目组升降级"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM project_groups WHERE id = ?', (project_id,))
    project = cursor.fetchone()
    if not project:
        raise Exception('项目组不存在')

    cursor.execute('SELECT * FROM project_levels WHERE id = ?', (new_level_id,))
    new_level = cursor.fetchone()
    if not new_level:
        raise Exception('新等级不存在')

    cursor.execute('SELECT * FROM project_levels WHERE id = ?', (project['level_id'],))
    old_level = cursor.fetchone()

    remaining_quota = project['current_quota'] - project['used_quota']
    remaining_hazardous = project['current_hazardous_quota'] - project['used_hazardous_quota']

    carry_over_amount = 0
    carry_over_type = 'proportional' if carry_over else 'reset'
    new_quota = new_level['monthly_quota']
    new_hazardous_quota = new_level['hazardous_quota']

    if carry_over and old_level and old_level['monthly_quota'] > 0:
        ratio = remaining_quota / old_level['monthly_quota']
        carry_over_amount = min(remaining_quota, new_level['monthly_quota'] * ratio)
        new_quota = new_level['monthly_quota'] + carry_over_amount

    cursor.execute('''
        UPDATE project_groups SET
            level_id = ?,
            current_quota = ?,
            current_hazardous_quota = ?,
            used_quota = 0,
            used_hazardous_quota = 0,
            updated_at = datetime('now','localtime')
        WHERE id = ?
    ''', (new_level_id, new_quota, new_hazardous_quota, project_id))

    cursor.execute('''
        INSERT INTO level_change_logs (
            project_id, old_level_id, new_level_id,
            old_quota, new_quota, carry_over_type, carry_over_amount, remark
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        project_id,
        project['level_id'],
        new_level_id,
        project['current_quota'],
        new_quota,
        carry_over_type,
        carry_over_amount,
        '按比例结转剩余额度' if carry_over else '升降级清零'
    ))

    conn.commit()

    old_name = old_level['level_name'] if old_level else '未知'
    add_operation_log(
        '等级额度', '升降级',
        f'{project["group_name"]} 从 {old_name} 变更为 {new_level["level_name"]}，{"按比例结转" if carry_over else "额度清零"}'
    )

    return True


def get_quota_usage(project_id):
    """获取项目组额度使用情况"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.*, l.level_name, l.monthly_quota, l.hazardous_quota
        FROM project_groups p
        LEFT JOIN project_levels l ON p.level_id = l.id
        WHERE p.id = ?
    ''', (project_id,))
    project = dict(cursor.fetchone()) if cursor.fetchone() else None

    cursor.execute('''
        SELECT c.*,
            old_l.level_name as old_level_name,
            new_l.level_name as new_level_name
        FROM level_change_logs c
        LEFT JOIN project_levels old_l ON c.old_level_id = old_l.id
        LEFT JOIN project_levels new_l ON c.new_level_id = new_l.id
        WHERE c.project_id = ?
        ORDER BY c.created_at DESC
    ''', (project_id,))
    change_logs = [dict(row) for row in cursor.fetchall()]

    return {'project': project, 'change_logs': change_logs}
