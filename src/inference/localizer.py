import cv2
import logging
import numpy as np

from dataclasses import dataclass
from pathlib import Path
from omegaconf import DictConfig

from src.utils.model import create_model
from src.utils.config import load_config
from src.utils.device import get_device
from src.utils.decorators import performance
from src.utils.distance import haversine_distance
from src.database.tile_db_manager import TileDatabaseManager # CONTAINS FAISS


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(name)s]: %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    uid: int
    score: float
    lon: float
    lat: float


@dataclass
class EstimatedGeoPosition:
    valid: bool
    lon: float = 0.0
    lat: float = 0.0
    eph: float = 0.0    # horizontal pos error


class Localizer:
    """Class to localize position."""
    def __init__(
        self,
        model_config: DictConfig,
        db_manager: TileDatabaseManager,
        device: str = None
    ):
        self.device = device
        self.db_manager = db_manager
        self.model = create_model(model_config, device)
        self.k = model_config.inference.top_k
        self.dist_epsilon = model_config.inference.dist_epsilon
        self.score_epsilon = model_config.inference.score_epsilon
        self.beta = model_config.inference.beta
        self.anchor_bonus_weight = model_config.inference.anchor_bonus_weight

    @performance
    def predict(self, image: np.ndarray) -> list[Prediction]:
        """Predicts passed frame image"""
        embedding = self.model.embed_image(image)
        scores, uids = self.db_manager.search(embedding, k=self.k)

        res = []

        # pre sorted by scores
        for uid, score in zip(uids[0], scores[0]):
            coords = self.db_manager.get_coords(int(uid))
            if coords is None:
                continue

            lon, lat = coords
            res.append(Prediction(
                uid=int(uid),
                score=float(score),
                lon=float(lon),
                lat=float(lat)
            ))

        return res

    def prune_acceptable_candidates(self, predictions: list[Prediction]) -> list[Prediction]:
        """
        Gets acceptable candidates in the format:
        
            [(score, (lon, lat)) ... ]
        
        by pruning from anchor based on haversine dist and score
        """
        anchor = predictions[0]     # top 1 
        anchor_coord = anchor.lon, anchor.lat
        candidates = []

        for prediction in predictions:
            prediction_coord = prediction.lon, prediction.lat
            dist = haversine_distance(anchor_coord, prediction_coord)
            if dist > self.dist_epsilon or prediction.score < self.score_epsilon:
                continue

            candidates.append(prediction)

        return candidates

    def get_weights(self, candidates: list[Prediction]) -> np.ndarray:
        """Gets the weight contribution for each candidate"""
        scores = np.array([candidate.score for candidate in candidates])

        logits = self.beta * (scores - scores.max())
        logits[0] += self.anchor_bonus_weight

        # softmax weighting 
        weights = np.exp(logits)
        weights /= weights.sum()

        return weights

    def calculate_weighted_position(
        self,
        candidates: list[Prediction],
        weights: np.ndarray,
    ) -> tuple[float, float]:
        """Calculate the final weighted position"""
        weighted_lon = 0.0
        weighted_lat = 0.0

        for weight, candidate in zip(weights, candidates):
            weighted_lon += weight * candidate.lon
            weighted_lat += weight * candidate.lat

        return weighted_lon, weighted_lat

    def compute_horizontal_std(
        self,
        center: tuple[float, float],
        candidates: list[Prediction],
        weights: np.ndarray
    ) -> float:
        """Computes std of our weighted candidate locations"""
        dists = []
        for candidate in candidates:
            candidate_coords = candidate.lon, candidate.lat
            dists.append(haversine_distance(center, candidate_coords))

        dists = np.asarray(dists, dtype=float)
        var = np.sum(weights * dists ** 2)
        horizontal_std = np.sqrt(var)

        return float(horizontal_std)

    def calculate_max_score(self,predictions: list[Prediction]) -> float:
        """Helper to calculate the max score when everything is filtered"""
        max_score = 0
        for prediction in predictions:
            max_score = max(prediction.score, max_score)
        return max_score

    def estimate_position(self, predictions: list[Prediction]) -> EstimatedGeoPosition:
        """Based on the top k predictions, make a location estimate"""
        if not predictions:
            return EstimatedGeoPosition(valid=False)

        candidates = self.prune_acceptable_candidates(predictions)

        if len(candidates) == 0:
            max_score = self.calculate_max_score(predictions)
            logger.info(f"Localization skipped: no candidates passed. Highest score: {max_score}")
            return EstimatedGeoPosition(valid=False)

        weights = self.get_weights(candidates)
        center = self.calculate_weighted_position(candidates, weights)
        horizontal_std = self.compute_horizontal_std(center, candidates, weights)

        est_lon, est_lat = center

        return EstimatedGeoPosition(
            valid=True,
            lon=est_lon,
            lat=est_lat,
            eph=horizontal_std
        )

def main(args=None):
    if args == "onnx":
        path = "src/config/default_onnx.yaml"
    else:
        path = "src/config/default.yaml"

    preprocessing_config_path = Path("src/config/preprocess.yaml")
    model_config_path = Path(path)

    model_config = load_config(model_config_path)
    preprocessing_config = load_config(preprocessing_config_path)
    device = get_device()

    db_manager = TileDatabaseManager(
        db_path=preprocessing_config.output.db,
        faiss_path=preprocessing_config.output.faiss,
        embedding_dim=model_config.model.embedding_dim
    )

    localizer = Localizer(model_config, db_manager, device)

    image = cv2.imread("data/query4.png") # ex
    res = localizer.predict(image)
    print(res)


if __name__ == "__main__":
    main("onnx")
