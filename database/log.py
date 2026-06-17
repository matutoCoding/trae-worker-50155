from database.db import get_conn, add_operation_log


def list_logs(module=None, action=None, keyword=None, page=1, page_size=20):
    """获取操作日志列表"""
    conn = get_conn()
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if module:
        where_clauses.append('module = ?')
        params.append(module)

    if action:
        where_clauses.append('action = ?')
        params.append(action)

    if keyword:
        where_clauses.append('detail LIKE ?')
        params.append(f'%{keyword}%')

    where_sql = ''
    if where_clauses:
        where_sql = 'WHERE ' + ' AND '.join(where_clauses)

    cursor.execute(f'SELECT COUNT(*) as total FROM operation_logs {where_sql}', params)
    total = cursor.fetchone()['total']

    offset = (page - 1) * page_size
    cursor.execute(
        f'SELECT * FROM operation_logs {where_sql} ORDER BY created_at DESC LIMIT ? OFFSET ?',
        params + [page_size, offset]
    )
    data = [dict(row) for row in cursor.fetchall()]

    return {'data': data, 'total': total, 'page': page, 'page_size': page_size}


def add_log(module, action, detail, operator='system'):
    """添加操作日志"""
    add_operation_log(module, action, detail, operator)
