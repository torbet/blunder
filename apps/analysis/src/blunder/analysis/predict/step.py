import torch

from blunder.analysis.core.model import DEVICE, Detector
from blunder.analysis.core.pipeline import PipelineContext, PipelineStep
from blunder.analysis.core.registry import Registry
from blunder.shared.analysis.predict import PredictConfig
from blunder.shared.models.analysis import LABELS, GamePredictionBase, MovePredictionBase


class PredictStep(PipelineStep):
    def __init__(self, config: PredictConfig) -> None:
        manifest, weights = Registry.create().load(config.version)
        self.model = Detector(manifest.config.model).to(DEVICE)
        self.model.load_state_dict(weights)
        self.model.eval()

    @torch.inference_mode()
    async def run(self, ctx: PipelineContext) -> None:
        games = ctx.games
        moves, outcomes = self.model([Detector.encode(game) for game in games])
        cheating = moves.sigmoid().split([len(game.moves) for game in games])

        for game, probabilities, outcome in zip(games, cheating, outcomes.softmax(-1).tolist(), strict=True):
            for move, probability in zip(game.moves, probabilities.tolist(), strict=True):
                move.predictions.append(MovePredictionBase(analysis_id=ctx.analysis.id, cheating=probability))

            game.predictions.append(
                GamePredictionBase(analysis_id=ctx.analysis.id, **dict(zip(LABELS.values(), outcome, strict=True)))
            )
