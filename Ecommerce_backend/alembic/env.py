from logging.config import fileConfig
+import os
+import sys
+
+from sqlalchemy import engine_from_config
+from sqlalchemy import pool
+
+from alembic import context
+
+# ensure project root on path
+sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
+
+# this is the Alembic Config object, which provides
+# access to the values within the .ini file in use.
+config = context.config
+
+# Interpret the config file for Python logging.
+fileConfig(config.config_file_name)
+
+from app.db.base_class import Base  # noqa: E402
+
+# target_metadata for 'autogenerate'
+target_metadata = Base.metadata
+
+
+def get_url():
+    return os.getenv("DATABASE_URL")
+
+
+def run_migrations_offline():
+    url = get_url()
+    context.configure(
+        url=url,
+        target_metadata=target_metadata,
+        literal_binds=True,
+        dialect_opts={"paramstyle": "named"},
+    )
+
+    with context.begin_transaction():
+        context.run_migrations()
+
+
+def run_migrations_online():
+    configuration = config.get_section(config.config_ini_section)
+    configuration["sqlalchemy.url"] = get_url()
+
+    connectable = engine_from_config(
+        configuration,
+        prefix="sqlalchemy.",
+        poolclass=pool.NullPool,
+    )
+
+    with connectable.connect() as connection:
+        context.configure(
+            connection=connection, target_metadata=target_metadata
+        )
+
+        with context.begin_transaction():
+            context.run_migrations()
+
+
+if context.is_offline_mode():
+    run_migrations_offline()
+else:
+    run_migrations_online()
+
