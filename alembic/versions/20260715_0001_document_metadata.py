"""Create durable document metadata table.

Revision ID: 20260715_0001
Revises:
Create Date: 2026-07-15
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260715_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("processing_stage", sa.String(length=32), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("character_count", sa.BigInteger(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=True),
        sa.Column("chroma_collection", sa.String(length=255), nullable=True),
        sa.Column("embedding_model", sa.String(length=512), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("file_size_bytes >= 0", name="ck_documents_file_size_nonnegative"),
        sa.CheckConstraint("page_count IS NULL OR page_count >= 0", name="ck_documents_page_count_nonnegative"),
        sa.CheckConstraint("character_count IS NULL OR character_count >= 0", name="ck_documents_character_count_nonnegative"),
        sa.CheckConstraint("chunk_count IS NULL OR chunk_count >= 0", name="ck_documents_chunk_count_nonnegative"),
        sa.CheckConstraint(
            "status IN ('processing', 'ready', 'failed')",
            name="ck_documents_status_value",
        ),
        sa.CheckConstraint(
            "processing_stage IN ('received', 'stored', 'extracting', 'cleaning', 'chunking', 'embedding', 'indexing', 'complete', 'failed')",
            name="ck_documents_processing_stage_value",
        ),
        sa.CheckConstraint(
            "status != 'ready' OR (processing_stage = 'complete' AND page_count IS NOT NULL AND character_count IS NOT NULL AND chunk_count IS NOT NULL AND indexed_at IS NOT NULL)",
            name="ck_documents_ready_metadata",
        ),
        sa.CheckConstraint(
            "status != 'failed' OR (processing_stage = 'failed' AND error_code IS NOT NULL)",
            name="ck_documents_failed_metadata",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sha256"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_documents_created_at", "documents", ["created_at"], unique=False)
    op.create_index("ix_documents_filename", "documents", ["filename"], unique=False)
    op.create_index("ix_documents_status", "documents", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_filename", table_name="documents")
    op.drop_index("ix_documents_created_at", table_name="documents")
    op.drop_table("documents")
