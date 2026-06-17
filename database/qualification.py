from database.db import get_conn, add_operation_log


def list_qualifications(keyword=None, status=None, project_id=None, page=1, page_size=20):
    """获取危化品资质列表"""
    conn = get_conn()
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if keyword:
        where_clauses.append('(holder_name LIKE ? OR certificate_no LIKE ? OR project_name LIKE ? OR qualification_type LIKE ?)')
        params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])

    if status:
        where_clauses.append('status = ?')
        params.append(status)

    if project_id:
        where_clauses.append('project_id = ?')
        params.append(project_id)

    where_sql = ''
    if where_clauses:
        where_sql = 'WHERE ' + ' AND '.join(where_clauses)

    cursor.execute(f'SELECT COUNT(*) as total FROM hazardous_qualifications {where_sql}', params)
    total = cursor.fetchone()['total']

    offset = (page - 1) * page_size
    cursor.execute(
        f'SELECT * FROM hazardous_qualifications {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?',
        params + [page_size, offset]
    )
    data = [dict(row) for row in cursor.fetchall()]

    return {'data': data, 'total': total, 'page': page, 'page_size': page_size}


def get_qualification(qual_id):
    """获取单个资质"""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM hazardous_qualifications WHERE id = ?', (qual_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def create_qualification(data):
    """新增资质"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO hazardous_qualifications (
            project_id, project_name, qualification_type, certificate_no,
            issue_date, expiry_date, issuing_authority, holder_name,
            holder_id_card, status, remark
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('project_id'),
        data.get('project_name'),
        data['qualification_type'],
        data['certificate_no'],
        data.get('issue_date'),
        data.get('expiry_date'),
        data.get('issuing_authority'),
        data.get('holder_name'),
        data.get('holder_id_card'),
        data.get('status', 'valid'),
        data.get('remark')
    ))

    conn.commit()
    qual_id = cursor.lastrowid

    holder = data.get('holder_name') or data.get('certificate_no')
    add_operation_log('危化品资质', '新增', f'新增资质: {data["qualification_type"]} - {holder}')

    return qual_id


def update_qualification(qual_id, data):
    """更新资质"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE hazardous_qualifications SET
            project_id = ?, project_name = ?, qualification_type = ?,
            certificate_no = ?, issue_date = ?, expiry_date = ?,
            issuing_authority = ?, holder_name = ?, holder_id_card = ?,
            status = ?, remark = ?, updated_at = datetime('now','localtime')
        WHERE id = ?
    ''', (
        data.get('project_id'),
        data.get('project_name'),
        data['qualification_type'],
        data['certificate_no'],
        data.get('issue_date'),
        data.get('expiry_date'),
        data.get('issuing_authority'),
        data.get('holder_name'),
        data.get('holder_id_card'),
        data.get('status', 'valid'),
        data.get('remark'),
        qual_id
    ))

    conn.commit()

    holder = data.get('holder_name') or data.get('certificate_no')
    add_operation_log('危化品资质', '修改', f'修改资质: {data["qualification_type"]} - {holder}')

    return cursor.rowcount


def delete_qualification(qual_id):
    """删除资质"""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT qualification_type, holder_name, certificate_no FROM hazardous_qualifications WHERE id = ?',
        (qual_id,)
    )
    qual = cursor.fetchone()

    cursor.execute('DELETE FROM hazardous_qualifications WHERE id = ?', (qual_id,))
    conn.commit()

    if qual:
        holder = qual['holder_name'] or qual['certificate_no']
        add_operation_log('危化品资质', '删除', f'删除资质: {qual["qualification_type"]} - {holder}')

    return cursor.rowcount
