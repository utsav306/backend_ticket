import os
import sys
from logging.config import fileConfig

from alembic import context

# Ensure the project root is on sys.path so "app" can be imported when
# Alembic runs from the alembic/ directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, Base  # noqa: E402
from app.config import settings  # noqa: E402
# Import all models so Alembic can detect them
from app.models import User, Event, Booking  # noqa: E402

# this is the Alembic Config object, which provides access to the values within
# the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
	fileConfig(config.config_file_name)

# Set target metadata for 'autogenerate' support
target_metadata = Base.metadata

# If sqlalchemy.url isn't set in alembic.ini, set it from app settings
if not config.get_main_option("sqlalchemy.url"):
	config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
	"""Run migrations in 'offline' mode.

	This configures the context with just a URL and not an Engine, though an
	Engine is acceptable here as well. By skipping the Engine creation we don't
	even need a DBAPI to be available.
	"""

	url = config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL
	context.configure(
		url=url,
		target_metadata=target_metadata,
		literal_binds=True,
		dialect_opts={"paramstyle": "named"},
	)

	with context.begin_transaction():
		context.run_migrations()


def run_migrations_online() -> None:
	"""Run migrations in 'online' mode."""

	# Use the application's Engine to ensure identical connection params
	connectable = engine

	with connectable.connect() as connection:
		context.configure(connection=connection, target_metadata=target_metadata)

		with context.begin_transaction():
			context.run_migrations()


if context.is_offline_mode():
	run_migrations_offline()
else:
	run_migrations_online()
