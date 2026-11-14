from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from blunder.api.core.database import Base
from blunder.shared.analysis import PipelineConfig


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    config: Mapped[PipelineConfig] = mapped_column(JSONB)


class Feature(Base):
    __tablename__ = "features"
    __table_args__ = (ForeignKeyConstraint(["game_id", "ply"], ["moves.game_id", "moves.ply"], ondelete="CASCADE"),)

    game_id: Mapped[UUID] = mapped_column(ForeignKey("games.id"), primary_key=True)
    analysis_id: Mapped[UUID] = mapped_column(ForeignKey("analyses.id"), primary_key=True)
    ply: Mapped[int] = mapped_column(primary_key=True)

    evaluation: Mapped[int | None]
    best: Mapped[str | None]

    probability: Mapped[float | None]
    entropy: Mapped[float | None]
    ponder: Mapped[float | None]

    win: Mapped[float | None]
    draw: Mapped[float | None]
    loss: Mapped[float | None]
