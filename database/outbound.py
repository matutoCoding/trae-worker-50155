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
