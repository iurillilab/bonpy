from datetime import datetime

from bonpy.experiment import Experiment

# filepath = "/Users/vigji/code/bonpy/tests/assets/test_dataset/M1/20231201/095001"


def test_experiment_loading_112023(asset_moviedata_folder):
    exp = Experiment.load_112023(asset_moviedata_folder)

    assert exp.data_dict is not None
    assert exp.metadata.timestamp == datetime(2023, 12, 14, 16, 27, 20)
    assert exp.metadata.animal_id == "M13"
    assert exp.metadata.paradigm_id == "test_dataset"
    assert exp.metadata.session_id == "20231214/162720"
    assert exp.size_gb >= 0.0011
