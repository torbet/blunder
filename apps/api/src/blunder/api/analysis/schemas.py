from blunder.shared.models.analysis import Analysis, AnalysisBase, Feature, FeatureBase


class AnalysisRead(Analysis): ...


class AnalysisCreate(AnalysisBase): ...


class FeatureRead(Feature): ...


class FeatureCreate(FeatureBase):
    ply: int
