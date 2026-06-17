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


def count_qual_stats():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT status, expiry_date FROM hazardous_qualifications')
    rows = cursor.fetchall()

    from datetime import date as _date
    today = _date.today()
    valid = 0
    expired = 0
    soon = 0

    for row in rows:
        is_expired = False
        is_soon = False
        if row['expiry_date']:
            try:
                from datetime import datetime as _dt
                exp = _dt.strptime(row['expiry_date'], '%Y-%m-%d').date()
                if exp < today:
                    is_expired = True
                elif (exp - today).days < 30:
                    is_soon = True
            except Exception:
                pass

        if is_expired or row['status'] == 'expired':
            expired += 1
        elif row['status'] == 'valid' and is_soon:
            soon += 1
            valid += 1
        elif row['status'] == 'valid':
            valid += 1

    return {'valid': valid, 'expired': expired, 'soon': soon, 'total': len(rows)}


def check_project_hazardous_valid(project_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM hazardous_qualifications
        WHERE project_id = ?
        ORDER BY created_at DESC
    ''', (project_id,))
    rows = cursor.fetchall()

    if not rows:
        return {
            'has_qual': False,
            'error_type': 'no_registration',
            'title': '未登记危化品资质',
            'reason': '该项目组尚未在系统中登记任何危化品资质，暂不允许出库危化品。\n\n请先前往「变更留痕 → 危化品资质」页面完成资质登记后再操作。',
            'qual': None,
        }

    from datetime import date as _date, datetime as _dt
    today = _date.today()

    best_qual = None
    best_status = None

    for r in rows:
        r = dict(r)
        status = r['status']
        is_expired = False
        is_soon = False
        exp_date_obj = None
        if r['expiry_date']:
            try:
                exp_date_obj = _dt.strptime(r['expiry_date'], '%Y-%m-%d').date()
                if exp_date_obj < today:
                    is_expired = True
                elif (exp_date_obj - today).days < 30:
                    is_soon = True
            except Exception:
                pass
        r['_exp_date_obj'] = exp_date_obj

        if is_expired:
            effective_status = 'expired'
        elif status == 'expired':
            effective_status = 'expired'
        elif status == 'valid':
            effective_status = 'valid'
        else:
            effective_status = status

        if effective_status == 'valid' and not is_expired:
            if not best_qual or is_soon:
                best_qual = r
                best_status = 'soon' if is_soon else 'valid'
                if best_status == 'valid':
                    break
        elif effective_status == 'expired':
            if not best_qual or best_status != 'soon':
                if best_status != 'valid':
                    best_qual = r
                    best_status = 'expired'
        elif not best_qual:
            best_qual = r
            best_status = effective_status

    if best_status == 'valid':
        return {'has_qual': True, 'reason': None, 'qual': best_qual}

    if best_status == 'soon':
        days = None
        exp_date = None
        cert_no = None
        if best_qual:
            exp_date = best_qual.get('expiry_date')
            cert_no = best_qual.get('certificate_no')
            if best_qual.get('_exp_date_obj'):
                days = (best_qual['_exp_date_obj'] - today).days
        msg_parts = ['该项目组危化品资质即将到期']
        if days is not None:
            msg_parts.append(f'（剩余 {days} 天）')
        if exp_date:
            msg_parts.append(f'，有效期至 {exp_date}')
        if cert_no:
            msg_parts.append(f'（证书编号：{cert_no}）')
        msg_parts.append('\n请尽快联系相关部门办理续期手续。')
        msg = ''.join(msg_parts)
        return {'has_qual': True, 'reason': msg, 'qual': best_qual, 'warning': True}

    if best_status == 'expired' and best_qual:
        exp_date = best_qual.get('expiry_date') or '-'
        cert_no = best_qual.get('certificate_no') or '-'
        qual_type = best_qual.get('qualification_type') or '危化品资质'
        expired_days = None
        if best_qual.get('_exp_date_obj'):
            expired_days = (today - best_qual['_exp_date_obj']).days
        msg_parts = [f'该项目组「{qual_type}」已过期，不允许出库危化品。']
        msg_parts.append(f'\n\n证书编号：{cert_no}')
        msg_parts.append(f'\n有效期至：{exp_date}')
        if expired_days is not None:
            msg_parts.append(f'\n已过期：{expired_days} 天')
        msg_parts.append('\n\n下一步操作：请立即联系相关人员办理资质续期，待续期成功后再发起出库。')
        return {
            'has_qual': False,
            'error_type': 'expired',
            'title': '危化品资质已过期',
            'reason': ''.join(msg_parts),
            'qual': best_qual,
        }

    if best_qual and best_qual.get('status') == 'pending':
        return {
            'has_qual': False,
            'error_type': 'pending',
            'title': '危化品资质待审批',
            'reason': '该项目组危化品资质当前为「待审批」状态，审批通过前暂不允许出库危化品。\n请联系管理员完成资质审批后再操作。',
            'qual': best_qual,
        }

    return {
        'has_qual': False,
        'error_type': 'no_valid',
        'title': '无有效危化品资质',
        'reason': '该项目组当前无有效的危化品资质，暂不允许出库危化品。\n请前往「变更留痕 → 危化品资质」页面核对并办理。',
        'qual': best_qual,
    }
