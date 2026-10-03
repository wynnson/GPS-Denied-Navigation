from pathlib import Path
from omegaconf import DictConfig

from src.preprocessing.raster_splitter import embed_raster
from src.utils.device import get_device
from src.utils.config import load_config
from src.utils.model import create_model
from src.utils.decorators import performance
from src.database.tile_db_manager import TileDatabaseManager # CONTAINS FAISS


@performance
def preprocess(
    model_config: DictConfig,
    preprocessing_config: DictConfig, 
    db_manager: TileDatabaseManager
):
    """Runs the preprocessing pipeline."""
    device = get_device()
    model = create_model(model_config, device)

    try:
        embed_raster(
            file_path=preprocessing_config.raster.file_path,
            model=model,
            db_manager=db_manager,
            stride=preprocessing_config.raster.stride,
            window_size=preprocessing_config.raster.window_size,
            batch_size=preprocessing_config.raster.batch_size,
            dst_crs=preprocessing_config.raster.dst_crs,
        )

    finally:
        db_manager.close()
        db_size = Path(preprocessing_config.output.db).stat().st_size
        faiss_size = Path(preprocessing_config.output.db).stat().st_size

        print(f"SQLite DB: {db_size / (1024**2):.4f} MB")
        print(f"FAISS index: {faiss_size / (1024**2):.4f} MB")
        print(f"Total: {(db_size + faiss_size) / (1024**2):.4f} MB")


def main(args=None):
    preprocess_config_path = Path("src/config/preprocess.yaml")
    model_config_path = Path("src/config/default.yaml")

    preprocessing_config = load_config(preprocess_config_path)
    model_config = load_config(model_config_path)

    db_manager = TileDatabaseManager(
        db_path=preprocessing_config.output.db,
        faiss_path=preprocessing_config.output.faiss,
        embedding_dim=model_config.model.embedding_dim
    )

    preprocess(model_config, preprocessing_config, db_manager)


if __name__ == "__main__":
    main()

