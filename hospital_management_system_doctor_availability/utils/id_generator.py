"""ID generation helpers."""


def get_next_id(cursor, table_name: str, id_column: str, prefix: str, width: int = 3) -> str:
    query = f"""
        SELECT NVL(MAX(TO_NUMBER(SUBSTR({id_column}, {len(prefix) + 1}))), 0) + 1
        FROM {table_name}
        WHERE REGEXP_LIKE({id_column}, '^{prefix}[0-9]+$')
    """
    cursor.execute(query)
    next_num = cursor.fetchone()[0]
    return f"{prefix}{str(next_num).zfill(width)}"
