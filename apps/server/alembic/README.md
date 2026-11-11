# Migrações

Toda tabela de negócio tenant-scoped deve:

1. Herdar `TenantScopedMixin` no modelo SQLAlchemy.
2. Ter `institution_id` obrigatório com FK para `institutions.id`.
3. Chamar `SELECT docflow_enable_tenant_rls('<tabela>')` na própria migração
   depois de criar a tabela.

A API ou worker deve executar `SET LOCAL app.current_institution_id = '<uuid>'`
antes de consultar uma tabela protegida pelo RLS.
