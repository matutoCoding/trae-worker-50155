from database.db import get_conn, add_operation_log


def list_batches(keyword=None, is_hazardous=None, page=1, page_size=20):
    """获取试剂批次列表"""
    conn = get_conn()
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if keyword:
        where_clauses.append('(reagent_name LIKE ? OR batch_no LIKE ? OR supplier LIKE ?)')
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])

    if is_hazardous is not None and is_hazardous != '':
        where_clauses.append('is_hazardous = ?')
        params.append(1 if is_hazardous else 0)

    where_sql = ''
    if where_clauses:
        where_sql = 'WHERE ' + ' AND '.join(where_clauses)

    cursor.execute(f'SELECT COUNT(*) as total FROM reagent_batches {where_sql}', params)
    total = cursor.fetchone()['total']

    offset = (page - 1) * page_size
    cursor.execute(
        f'SELECT * FROM reagent_batches {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?',
        params + [page_size, offset]
    )
    data = [dict(row) for row in cursor.fetchall()]

    return {'data': data, 'total': total, 'page': page, 'page_size': page_size}


def get_batch(batch_id):
    """获取单个试剂批次"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reagent_batches WHERE id = ?', (batch_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def create_batch(data):
    """新增试剂批次"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO reagent_batches (
            reagent_name, batch_no, specification, unit, total_quantity,
            remaining_quantity, production_date, expiry_date, supplier,
            storage_condition, is_hazardous, hazard_level, remark
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['reagent_name'],
        data['batch_no'],
        data.get('specification'),
        data['unit'],
        data['total_quantity'],
        data['total_quantity'],
        data.get('production_date'),
        data.get('expiry_date'),
        data.get('supplier'),
        data.get('storage_condition'),
        1 if data.get('is_hazardous') else 0,
        data.get('hazard_level'),
        data.get('remark')
    ))

    conn.commit()
    batch_id = cursor.lastrowid

    add_operation_log('试剂批次', '新增', f'新增试剂批次: {data["reagent_name"]} ({data["batch_no"]})')

    return batch_id


def update_batch(batch_id, data):
    """更新试剂批次"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE reagent_batches SET
            reagent_name = ?, batch_no = ?, specification = ?, unit = ?,
            total_quantity = ?, production_date = ?, expiry_date = ?,
            supplier = ?, storage_condition = ?, is_hazardous = ?,
            hazard_level = ?, remark = ?, updated_at = datetime('now','localtime')
        WHERE id = ?
    ''', (
        data['reagent_name'],
        data['batch_no'],
        data.get('specification'),
        data['unit'],
        data['total_quantity'],
        data.get('production_date'),
        data.get('expiry_date'),
        data.get('supplier'),
        data.get('storage_condition'),
        1 if data.get('is_hazardous') else 0,
        data.get('hazard_level'),
        data.get('remark'),
        batch_id
    ))

    conn.commit()
    add_operation_log('试剂批次', '修改', f'修改试剂批次: {data["reagent_name"]} ({data["batch_no"]})')

    return cursor.rowcount


def delete_batch(batch_id):
    """删除试剂批次"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('SELECT reagent_name, batch_no FROM reagent_batches WHERE id = ?', (batch_id,))
    batch = cursor.fetchone()

    cursor.execute('DELETE FROM reagent_batches WHERE id = ?', (batch_id,))
    conn.commit()

    if batch:
        add_operation_log('试剂批次', '删除', f'删除试剂批次: {batch["reagent_name"]} ({batch["batch_no"]})')

    return cursor.rowcount
