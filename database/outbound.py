from database.db import get_conn, add_operation_log


def list_outbound(keyword=None, batch_id=None, project_id=None, page=1, page_size=20):
    """获取出库记录列表"""
    conn = get_conn()
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if keyword:
        where_clauses.append('(receiver LIKE ? OR purpose LIKE ? OR o.remark LIKE ?)')
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])

    if batch_id:
        where_clauses.append('o.batch_id = ?')
        params.append(batch_id)

    if project_id:
        where_clauses.append('o.project_id = ?')
        params.append(project_id)

    where_sql = ''
    if where_clauses:
        where_sql = 'WHERE ' + ' AND '.join(where_clauses)

    cursor.execute(f'SELECT COUNT(*) as total FROM outbound_records o {where_sql}', params)
    total = cursor.fetchone()['total']

    offset = (page - 1) * page_size
    cursor.execute(f'''
        SELECT o.*, b.reagent_name, b.batch_no, b.unit, b.is_hazardous
        FROM outbound_records o
        LEFT JOIN reagent_batches b ON o.batch_id = b.id
        {where_sql}
        ORDER BY o.outbound_date DESC
        LIMIT ? OFFSET ?
    ''', params + [page_size, offset])

    data = [dict(row) for row in cursor.fetchall()]

    return {'data': data, 'total': total, 'page': page, 'page_size': page_size}


def get_outbound(outbound_id):
    """获取单个出库记录"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.*, b.reagent_name, b.batch_no, b.unit, b.is_hazardous
        FROM outbound_records o
        LEFT JOIN reagent_batches b ON o.batch_id = b.id
        WHERE o.id = ?
    ''', (outbound_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def create_outbound(data):
    """新增出库记录"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM reagent_batches WHERE id = ?', (data['batch_id'],))
    batch = cursor.fetchone()
    if not batch:
        raise Exception('批次不存在')

    if batch['remaining_quantity'] < data['quantity']:
        raise Exception(f'库存不足，当前剩余 {batch["remaining_quantity"]} {batch["unit"]}')

    project = None
    project_name = data.get('project_name')
    if data.get('project_id'):
        cursor.execute('SELECT * FROM project_groups WHERE id = ?', (data['project_id'],))
        project = cursor.fetchone()
        if project:
            project_name = project['group_name']

    cursor.execute('''
        INSERT INTO outbound_records (
            batch_id, quantity, project_id, project_name, receiver,
            outbound_date, purpose, remark
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['batch_id'],
        data['quantity'],
        data.get('project_id'),
        project_name,
        data['receiver'],
        data.get('outbound_date'),
        data.get('purpose'),
        data.get('remark')
    ))

    cursor.execute(
        'UPDATE reagent_batches SET remaining_quantity = remaining_quantity - ? WHERE id = ?',
        (data['quantity'], data['batch_id'])
    )

    if project:
        if batch['is_hazardous']:
            cursor.execute(
                'UPDATE project_groups SET used_hazardous_quota = used_hazardous_quota + ? WHERE id = ?',
                (data['quantity'], data['project_id'])
            )
        else:
            cursor.execute(
                'UPDATE project_groups SET used_quota = used_quota + ? WHERE id = ?',
                (data['quantity'], data['project_id'])
            )

    conn.commit()
    outbound_id = cursor.lastrowid

    dest = project_name if project_name else '未指定'
    add_operation_log(
        '拆分出库', '出库',
        f'{batch["reagent_name"]} ({batch["batch_no"]}) 出库 {data["quantity"]} {batch["unit"]}，去向: {dest}'
    )

    return outbound_id


def get_outbound_by_batch(batch_id):
    """获取某个批次的所有出库记录"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.*, b.reagent_name, b.batch_no, b.unit
        FROM outbound_records o
        LEFT JOIN reagent_batches b ON o.batch_id = b.id
        WHERE o.batch_id = ?
        ORDER BY o.outbound_date DESC
    ''', (batch_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_distribution(batch_id):
    """获取批次的去向好分布"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            COALESCE(project_name, '未分配') as destination,
            SUM(quantity) as total_quantity,
            COUNT(*) as outbound_count
        FROM outbound_records
        WHERE batch_id = ?
        GROUP BY project_name
        ORDER BY total_quantity DESC
    ''', (batch_id,))
    distribution = [dict(row) for row in cursor.fetchall()]

    cursor.execute('SELECT total_quantity, remaining_quantity, unit FROM reagent_batches WHERE id = ?', (batch_id,))
    batch = dict(cursor.fetchone())

    total_outbound = sum(d['total_quantity'] for d in distribution)

    return {
        'distribution': distribution,
        'batch': batch,
        'total_outbound': total_outbound
    }


def get_project_monthly_outbound(project_id, year_month=None):
    conn = get_conn()
    cursor = conn.cursor()

    where_sql = 'WHERE o.project_id = ?'
    params = [project_id]

    if year_month:
        where_sql += " AND substr(o.outbound_date, 1, 7) = ?"
        params.append(year_month)

    cursor.execute(f'''
        SELECT o.*, b.reagent_name, b.batch_no, b.unit, b.is_hazardous
        FROM outbound_records o
        LEFT JOIN reagent_batches b ON o.batch_id = b.id
        {where_sql}
        ORDER BY o.outbound_date DESC
    ''', params)
    records = [dict(row) for row in cursor.fetchall()]

    normal_records = [r for r in records if not r['is_hazardous']]
    hazard_records = [r for r in records if r['is_hazardous']]
    normal_total = sum(r['quantity'] for r in normal_records)
    hazard_total = sum(r['quantity'] for r in hazard_records)

    return {
        'records': records,
        'normal_records': normal_records,
        'hazard_records': hazard_records,
        'normal_total': normal_total,
        'hazard_total': hazard_total,
        'count': len(records)
    }


def get_project_monthly_settlement(project_id, year_month):
    from datetime import datetime as _dt, timedelta as _td
    conn = get_conn()
    cursor = conn.cursor()

    ym = year_month
    month_start_str = f'{ym}-01 00:00:00'
    y, m = ym.split('-')
    if int(m) == 12:
        next_ym = f'{int(y)+1}-01'
    else:
        next_ym = f'{y}-{int(m)+1:02d}'
    month_end_str = f'{next_ym}-01 00:00:00'

    cursor.execute('''
        SELECT * FROM project_groups WHERE id = ?
    ''', (project_id,))
    project = cursor.fetchone()
    if not project:
        return None
    project = dict(project)

    cursor.execute('''
        SELECT lcl.*,
            old_l.level_name as old_level_name,
            new_l.level_name as new_level_name
        FROM level_change_logs lcl
        LEFT JOIN project_levels old_l ON lcl.old_level_id = old_l.id
        LEFT JOIN project_levels new_l ON lcl.new_level_id = new_l.id
        WHERE lcl.project_id = ?
          AND lcl.created_at >= ?
          AND lcl.created_at < ?
        ORDER BY lcl.created_at ASC
    ''', (project_id, month_start_str, month_end_str))
    adjust_records = [dict(r) for r in cursor.fetchall()]

    cursor.execute('''
        SELECT lcl.*,
            old_l.level_name as old_level_name,
            new_l.level_name as new_level_name
        FROM level_change_logs lcl
        LEFT JOIN project_levels old_l ON lcl.old_level_id = old_l.id
        LEFT JOIN project_levels new_l ON lcl.new_level_id = new_l.id
        WHERE lcl.project_id = ?
          AND lcl.created_at < ?
        ORDER BY lcl.created_at DESC
        LIMIT 1
    ''', (project_id, month_start_str))
    last_change_before = cursor.fetchone()
    last_change_before = dict(last_change_before) if last_change_before else None

    cursor.execute(f'''
        SELECT o.*, b.reagent_name, b.batch_no, b.unit, b.is_hazardous
        FROM outbound_records o
        LEFT JOIN reagent_batches b ON o.batch_id = b.id
        WHERE o.project_id = ?
          AND o.outbound_date >= ?
          AND o.outbound_date < ?
        ORDER BY o.outbound_date DESC
    ''', (project_id, month_start_str, month_end_str))
    out_records = [dict(r) for r in cursor.fetchall()]

    normal_records = [r for r in out_records if not r['is_hazardous']]
    hazard_records = [r for r in out_records if r['is_hazardous']]
    normal_outbound = sum(r['quantity'] for r in normal_records)
    hazard_outbound = sum(r['quantity'] for r in hazard_records)

    def _trace_quota(project_dict, last_change, as_of):
        if last_change:
            begin_normal = last_change.get('new_quota') or last_change.get('old_quota') or project_dict['current_quota']
            begin_hazard = last_change.get('new_hazardous_quota')
            if begin_hazard is None:
                begin_hazard = last_change.get('old_hazardous_quota')
            if begin_hazard is None:
                begin_hazard = project_dict['current_hazardous_quota']
            return float(begin_normal), float(begin_hazard)
        cursor.execute('''
            SELECT level_rank, monthly_quota, hazardous_quota
            FROM project_levels WHERE id = ?
        ''', (project_dict['level_id'],))
        level = cursor.fetchone()
        if level:
            return float(level['monthly_quota']), float(level['hazardous_quota'])
        return float(project_dict['current_quota']), float(project_dict['current_hazardous_quota'])

    begin_normal_quota, begin_hazard_quota = _trace_quota(project, last_change_before, month_start_str)

    adj_normal_delta = 0.0
    adj_hazard_delta = 0.0
    for rec in adjust_records:
        old_n = rec.get('old_quota') or 0
        new_n = rec.get('new_quota') or 0
        adj_normal_delta += (new_n - old_n)
        old_h = rec.get('old_hazardous_quota') or 0
        new_h = rec.get('new_hazardous_quota') or 0
        adj_hazard_delta += (new_h - old_h)

    used_normal_sofar = float(project.get('used_quota') or 0)
    used_hazard_sofar = float(project.get('used_hazardous_quota') or 0)

    today_str = _dt.now().strftime('%Y-%m')
    is_current_month = (year_month == today_str)

    if is_current_month:
        end_normal_quota = float(project['current_quota'])
        end_hazard_quota = float(project['current_hazardous_quota'])
    else:
        end_normal_quota = begin_normal_quota + adj_normal_delta
        end_hazard_quota = begin_hazard_quota + adj_hazard_delta

    normal_remaining = end_normal_quota - used_normal_sofar if is_current_month else (
        begin_normal_quota + adj_normal_delta - normal_outbound)
    hazard_remaining = end_hazard_quota - used_hazard_sofar if is_current_month else (
        begin_hazard_quota + adj_hazard_delta - hazard_outbound)

    return {
        'project': project,
        'year_month': year_month,
        'begin_normal_quota': begin_normal_quota,
        'begin_hazard_quota': begin_hazard_quota,
        'normal_outbound': normal_outbound,
        'hazard_outbound': hazard_outbound,
        'adjust_normal_delta': adj_normal_delta,
        'adjust_hazard_delta': adj_hazard_delta,
        'end_normal_quota': end_normal_quota,
        'end_hazard_quota': end_hazard_quota,
        'normal_remaining': normal_remaining,
        'hazard_remaining': hazard_remaining,
        'adjust_records': adjust_records,
        'outbound_records': out_records,
        'normal_records': normal_records,
        'hazard_records': hazard_records,
        'is_current_month': is_current_month,
        'used_normal_sofar': used_normal_sofar,
        'used_hazard_sofar': used_hazard_sofar,
    }


def check_quota_overflow(project_id, batch_id, quantity):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM project_groups WHERE id = ?', (project_id,))
    project = cursor.fetchone()
    if not project:
        return {'overflow': False, 'reason': '项目不存在'}
    project = dict(project)

    cursor.execute('SELECT * FROM reagent_batches WHERE id = ?', (batch_id,))
    batch = cursor.fetchone()
    if not batch:
        return {'overflow': False, 'reason': '批次不存在'}
    batch = dict(batch)

    if batch['remaining_quantity'] < quantity:
        return {'overflow': True, 'type': 'stock',
                'reason': f'库存不足：需要 {quantity} {batch["unit"]}，剩余 {batch["remaining_quantity"]} {batch["unit"]}',
                'batch': batch, 'project': project}

    if batch['is_hazardous']:
        remain = project['current_hazardous_quota'] - project['used_hazardous_quota']
        if quantity > remain:
            return {
                'overflow': True,
                'type': 'hazard_quota',
                'reason': f"危化品额度不足：申请 {quantity}，剩余额度 {remain:.1f}，缺口 {quantity - remain:.1f}",
                'requested': quantity,
                'remaining': remain,
                'shortage': quantity - remain,
                'batch': batch,
                'project': project,
            }
    else:
        remain = project['current_quota'] - project['used_quota']
        if quantity > remain:
            return {
                'overflow': True,
                'type': 'normal_quota',
                'reason': f"普通试剂额度不足：申请 {quantity}，剩余额度 {remain:.1f}，缺口 {quantity - remain:.1f}",
                'requested': quantity,
                'remaining': remain,
                'shortage': quantity - remain,
                'batch': batch,
                'project': project,
            }

    return {'overflow': False, 'batch': batch, 'project': project}


def create_outbound_approval(data):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM reagent_batches WHERE id = ?', (data['batch_id'],))
    batch = cursor.fetchone()
    if not batch:
        raise Exception('批次不存在')
    batch = dict(batch)

    cursor.execute('SELECT * FROM project_groups WHERE id = ?', (data['project_id'],))
    project = cursor.fetchone()
    if not project:
        raise Exception('项目不存在')
    project = dict(project)

    if batch['is_hazardous']:
        remaining_quota = project['current_hazardous_quota'] - project['used_hazardous_quota']
    else:
        remaining_quota = project['current_quota'] - project['used_quota']
    quota_shortage = max(0, data['quantity'] - remaining_quota)

    cursor.execute('''
        INSERT INTO outbound_approvals (
            batch_id, reagent_name, batch_no, quantity, unit,
            project_id, project_name, receiver, outbound_date, purpose, remark,
            is_hazardous, status, requested_amount, remaining_quota, quota_shortage,
            applicant
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
    ''', (
        data['batch_id'],
        batch['reagent_name'],
        batch['batch_no'],
        data['quantity'],
        batch['unit'],
        data['project_id'],
        project['group_name'],
        data['receiver'],
        data.get('outbound_date'),
        data.get('purpose'),
        data.get('remark'),
        1 if batch['is_hazardous'] else 0,
        data['quantity'],
        remaining_quota,
        quota_shortage,
        data.get('applicant') or data['receiver'],
    ))

    conn.commit()
    approval_id = cursor.lastrowid

    add_operation_log(
        '额度占用审批', '提交',
        f"{batch['reagent_name']} ({batch['batch_no']}) 申请 {data['quantity']} {batch['unit']}，去向 {project['group_name']}"
        f"（额度缺口 {quota_shortage:.1f}）"
    )
    return approval_id


def list_outbound_approvals(status=None, project_id=None, keyword=None, page=1, page_size=50):
    conn = get_conn()
    cursor = conn.cursor()

    where = []
    params = []
    if status:
        where.append('status = ?')
        params.append(status)
    if project_id:
        where.append('project_id = ?')
        params.append(project_id)
    if keyword:
        where.append('(reagent_name LIKE ? OR project_name LIKE ? OR receiver LIKE ?)')
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])

    where_sql = 'WHERE ' + ' AND '.join(where) if where else ''

    cursor.execute(f'SELECT COUNT(*) as cnt FROM outbound_approvals {where_sql}', params)
    total = cursor.fetchone()['cnt']

    offset = (page - 1) * page_size
    cursor.execute(f'''
        SELECT * FROM outbound_approvals
        {where_sql}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    ''', params + [page_size, offset])
    rows = [dict(r) for r in cursor.fetchall()]
    return {'data': rows, 'total': total, 'page': page, 'page_size': page_size}


def get_outbound_approval(approval_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM outbound_approvals WHERE id = ?', (approval_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def approve_outbound(approval_id, approver='管理员', note=None):
    from datetime import datetime as _dt
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM outbound_approvals WHERE id = ?', (approval_id,))
    approval = cursor.fetchone()
    if not approval:
        raise Exception('审批记录不存在')
    approval = dict(approval)
    if approval['status'] != 'pending':
        raise Exception(f'当前状态为「{approval["status"]}」，无法审批')

    cursor.execute('SELECT * FROM reagent_batches WHERE id = ?', (approval['batch_id'],))
    batch = cursor.fetchone()
    if not batch:
        raise Exception('关联批次不存在')
    batch = dict(batch)
    if batch['remaining_quantity'] < approval['quantity']:
        raise Exception(f"库存不足：剩余 {batch['remaining_quantity']} {batch['unit']}，需要 {approval['quantity']} {batch['unit']}")

    cursor.execute('SELECT * FROM project_groups WHERE id = ?', (approval['project_id'],))
    project = cursor.fetchone()
    if not project:
        raise Exception('关联项目组不存在')
    project = dict(project)

    cursor.execute(
        'UPDATE reagent_batches SET remaining_quantity = remaining_quantity - ? WHERE id = ?',
        (approval['quantity'], approval['batch_id'])
    )

    if approval['is_hazardous']:
        cursor.execute(
            'UPDATE project_groups SET used_hazardous_quota = used_hazardous_quota + ? WHERE id = ?',
            (approval['quantity'], approval['project_id'])
        )
    else:
        cursor.execute(
            'UPDATE project_groups SET used_quota = used_quota + ? WHERE id = ?',
            (approval['quantity'], approval['project_id'])
        )

    cursor.execute('''
        INSERT INTO outbound_records (
            batch_id, quantity, project_id, project_name, receiver,
            outbound_date, purpose, remark
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        approval['batch_id'],
        approval['quantity'],
        approval['project_id'],
        approval['project_name'],
        approval.get('receiver'),
        approval.get('outbound_date') or _dt.now().strftime('%Y-%m-%d %H:%M:%S'),
        approval.get('purpose'),
        approval.get('remark'),
    ))

    cursor.execute('''
        UPDATE outbound_approvals
           SET status = 'approved',
               approved_by = ?,
               approval_note = ?,
               approved_at = datetime('now', 'localtime')
         WHERE id = ?
    ''', (approver, note, approval_id))

    conn.commit()

    add_operation_log(
        '额度占用审批', '通过',
        f"{approval['reagent_name']} ({approval['batch_no']}) 审批通过 {approval['quantity']} {approval['unit']}，去向 {approval['project_name']}"
    )
    return True


def reject_outbound(approval_id, approver='管理员', note=None):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM outbound_approvals WHERE id = ?', (approval_id,))
    approval = cursor.fetchone()
    if not approval:
        raise Exception('审批记录不存在')
    approval = dict(approval)
    if approval['status'] != 'pending':
        raise Exception(f'当前状态为「{approval["status"]}」，无法拒绝')

    cursor.execute('''
        UPDATE outbound_approvals
           SET status = 'rejected',
               approved_by = ?,
               approval_note = ?,
               approved_at = datetime('now', 'localtime')
         WHERE id = ?
    ''', (approver, note, approval_id))
    conn.commit()

    add_operation_log(
        '额度占用审批', '拒绝',
        f"{approval['reagent_name']} ({approval['batch_no']}) 申请 {approval['quantity']} {approval['unit']} 被拒绝"
        + (f"，原因：{note}" if note else "")
    )
    return True


def count_approval_stats():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) as cnt FROM outbound_approvals GROUP BY status")
    rows = cursor.fetchall()
    result = {'pending': 0, 'approved': 0, 'rejected': 0, 'total': 0}
    for r in rows:
        result[r['status']] = r['cnt']
        result['total'] += r['cnt']
    return result
