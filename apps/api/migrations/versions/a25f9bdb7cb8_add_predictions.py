"""add predictions

Revision ID: a25f9bdb7cb8
Revises: b5881ffcf594
Create Date: 2026-11-14 18:05:14.887825

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a25f9bdb7cb8"
down_revision: str | Sequence[str] | None = "b5881ffcf594"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "game_predictions",
        sa.Column("game_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("neither", sa.Double(), nullable=False),
        sa.Column("white", sa.Double(), nullable=False),
        sa.Column("black", sa.Double(), nullable=False),
        sa.Column("both", sa.Double(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["analyses.id"], name=op.f("fk_game_predictions_analysis_id_analyses")
        ),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], name=op.f("fk_game_predictions_game_id_games")),
        sa.PrimaryKeyConstraint("game_id", "analysis_id", name=op.f("pk_game_predictions")),
    )
    op.create_table(
        "move_predictions",
        sa.Column("game_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_id", sa.Uuid(), nullable=False),
        sa.Column("ply", sa.Integer(), nullable=False),
        sa.Column("cheating", sa.Double(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["analyses.id"], name=op.f("fk_move_predictions_analysis_id_analyses")
        ),
        sa.ForeignKeyConstraint(
            ["game_id", "ply"],
            ["moves.game_id", "moves.ply"],
            name=op.f("fk_move_predictions_game_id_ply_moves"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], name=op.f("fk_move_predictions_game_id_games")),
        sa.PrimaryKeyConstraint("game_id", "analysis_id", "ply", name=op.f("pk_move_predictions")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("move_predictions")
    op.drop_table("game_predictions")
