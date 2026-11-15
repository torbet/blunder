from blunder.analysis.core.pipeline import PipelineContext, PipelineStep
from blunder.maia.core.maia import Maia
from blunder.shared.analysis.maia import MaiaConfig


class MaiaStep(PipelineStep):
    def __init__(self, config: MaiaConfig) -> None:
        self.maia = Maia(config.model, config.batch)

    async def run(self, ctx: PipelineContext) -> None:
        ctx.merge(self.maia.features(ctx.games))
