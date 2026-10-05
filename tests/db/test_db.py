from sqlalchemy import inspect

def test_tables_exists(db_engine):
    inspector = inspect(db_engine)
    tables = inspector.get_table_names()
    
    tables_expected = {'users', 'products', 'transactions'}
    assert tables_expected.issubset(set(tables))
    
def test_user_table_has_pk(db_engine):
    inspector = inspect(db_engine)
    pk = inspector.get_pk_constraint('users')
    
    assert pk is not None
    assert pk["constrained_columns"] == ["id"]

# def test_user
    