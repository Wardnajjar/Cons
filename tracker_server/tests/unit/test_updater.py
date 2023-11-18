from unittest.mock import MagicMock
from unittest.mock import call
from datetime import datetime
from bson import ObjectId
import pickle
import os

from pandas.testing import assert_frame_equal
import pandas as pd
import pytest

from app.recommender import Recommender as EPR
from app.tasks.updater import Updater


@pytest.fixture(scope="module")
def mocked_db():
    db = MagicMock()
    db.update = MagicMock()
    return db


class Model:
    def __init__(self, name):
        self.name = name


@pytest.fixture
def model():
    return Model(name="test_model")


@pytest.fixture(scope="module")
def updater_instance(mocked_db):
    updater = Updater("5f5b940f60a37c2b4012b971", mocked_db)
    return updater


def test_yesterday_powers(updater_instance):
    docs = [
        {
            "5f5b940f60a37c2b4012b973": 1,
            "5f5b940f60a37c2b4012b974": 0.1,
            "5f5b940f60a37c2b4012b975": 4,
        },
        {
            "5f5b940f60a37c2b4012b973": 6,
            "5f5b940f60a37c2b4012b974": 0.3,
            "5f5b940f60a37c2b4012b975": 0.4,
        },
        {
            "5f5b940f60a37c2b4012b973": 1,
            "5f5b940f60a37c2b4012b974": 8,
            "5f5b940f60a37c2b4012b975": 0.45,
        },
    ]
    updater_instance.db.get_docs = MagicMock(return_value=docs)
    res = updater_instance._yesterday_powers()
    output = pd.DataFrame(docs)
    assert_frame_equal(res, output)


def test_get_energys(updater_instance):
    docs = [
        {
            "5f5b940f60a37c2b4012b973": 1,
            "5f5b940f60a37c2b4012b974": 0.1,
            "5f5b940f60a37c2b4012b975": 4,
        },
        {
            "5f5b940f60a37c2b4012b973": 6,
            "5f5b940f60a37c2b4012b974": 0.3,
            "5f5b940f60a37c2b4012b975": 0.4,
        },
        {
            "5f5b940f60a37c2b4012b973": 1,
            "5f5b940f60a37c2b4012b974": 8,
            "5f5b940f60a37c2b4012b975": 0.45,
        },
    ]
    res = updater_instance._get_energys()
    output = pd.DataFrame(docs)
    assert_frame_equal(res, output)


def test_generate_yesterday_energys(updater_instance):
    appliances = [
        {"_id": ObjectId("5f5b940f60a37c2b4012b973"), "is_deleted": False, "energy": 1},
        {
            "_id": ObjectId("5f5b940f60a37c2b4012b974"),
            "is_deleted": False,
            "energy": 0.1,
        },
        {
            "_id": ObjectId("5f5b940f60a37c2b4012b975"),
            "is_deleted": False,
            "energy": 4.5,
        },
        {
            "_id": ObjectId("5f5b940f60a37c2b4012b976"),
            "is_deleted": True,
            "energy": 3.0,
        },
    ]
    powers_data = {
        "timestamp": [datetime(2023, 11, 16, 0, 0, 0), datetime(2023, 11, 16, 1, 0, 0)],
        "5f5b940f60a37c2b4012b973": [1.0, 2.0],
        "5f5b940f60a37c2b4012b974": [0.1, 0.2],
        "5f5b940f60a37c2b4012b975": [4.5, 4.6],
        "5f5b940f60a37c2b4012b976": [3.0, 3.1],
    }
    powers = pd.DataFrame(powers_data)

    energys = updater_instance._generate_yesterday_energys(appliances, powers)

    expected_energys = {
        "5f5b940f60a37c2b4012b973": 1,
        "5f5b940f60a37c2b4012b974": 0.1,
        "5f5b940f60a37c2b4012b975": 4.5,
    }

    assert energys == expected_energys


@pytest.mark.parametrize(
    ("date"),
    (
        (datetime(2023, 11, 16)),
        (datetime(2023, 11, 1)),
    ),
)
def test_update_energy(updater_instance, date):
    energys = {
        "5f5b940f60a37c2b4012b973": 1,
        "5f5b940f60a37c2b4012b974": 0.1,
        "5f5b940f60a37c2b4012b975": -4.5,
    }
    updater_instance._update_energy(energys, 0, date)
    if date.day == 1:
        updater_instance.db.update.assert_has_calls(
            [call("Users", "5f5b940f60a37c2b4012b971", "current_month_energy", 0)]
        )
    else:
        updater_instance.db.update.assert_has_calls(
            [call("Users", "5f5b940f60a37c2b4012b971", "current_month_energy", 5.6)]
        )


def test_dump_model(updater_instance, model):
    type = "test"
    app_id = "5f5b940f60a37c2b4012b975"
    updater_instance._dump_model(type, app_id, model)

    folder_path = "models_filesystem/test_models/5f5b940f60a37c2b4012b971"
    assert os.path.exists(folder_path)
    file_path = os.path.join(folder_path, "5f5b940f60a37c2b4012b975.pkl")
    file = open(file_path, "rb")
    output = pickle.load(file)
    assert isinstance(output, Model)


def test_apply_cluster(updater_instance, monkeypatch):
    app_id = "5f5b940f60a37c2b4012b973"
    e_type = 3
    powers = {app_id: [1.0, 2.0, 3.0, 4.0, 5.0]}

    updater_instance._dump_model = MagicMock()
    monkeypatch.setattr(EPR, "cluster", MagicMock(return_value="mocked_cluster"))

    updater_instance._apply_cluster(app_id, e_type, powers)

    EPR.cluster.assert_called_once_with(powers[app_id])
    updater_instance._dump_model.assert_called_once_with(
        "cluster", app_id, "mocked_cluster"
    )


def test_apply_forecast(updater_instance, monkeypatch):
    app_id = "5f5b940f60a37c2b4012b975"
    energys = {app_id: 4.5}
    forecast_model = MagicMock()
    forecast_threshold = 10.0
    updater_instance._dump_model.return_value = forecast_model
    monkeypatch.setattr(
        EPR,
        "energy_forecast",
        MagicMock(return_value=(forecast_model, forecast_threshold)),
    )

    updater_instance._apply_forecast(app_id, energys)

    updater_instance.db.update.assert_called_with(
        "Users",
        updater_instance.user_id,
        "appliances.$[elem].baseline_threshold",
        forecast_threshold,
        [{"elem._id": ObjectId(app_id)}],
    )
    updater_instance._dump_model.assert_called_with("forecast", app_id, forecast_model)


def test_run(updater_instance):
    updater_instance._yesterday_powers = MagicMock(return_value=pd.DataFrame())
    updater_instance._get_energys = MagicMock(return_value=pd.DataFrame())
    updater_instance._generate_yesterday_energys = MagicMock(return_value={})
    updater_instance._apply_cluster = MagicMock()
    updater_instance._apply_forecast = MagicMock()
    updater_instance.db.insert_doc = MagicMock()

    updater_instance.run()

    updater_instance._yesterday_powers.assert_called_once()
    updater_instance._get_energys.assert_called_once()
    updater_instance._generate_yesterday_energys.assert_called_once()
    expected_energys = updater_instance._generate_yesterday_energys.return_value
    appliances = updater_instance.db.get_doc.return_value["appliances"]
    for app in appliances:
        app_id = str(app["_id"])
        updater_instance._apply_cluster.assert_any_call(
            app_id, app["e_type"], updater_instance._yesterday_powers.return_value
        )
        updater_instance._apply_forecast.assert_any_call(app_id, expected_energys)

    expected_yesterday_energys = (
        updater_instance._generate_yesterday_energys.return_value
    )
    expected_yesterday_energys["user"] = ObjectId(updater_instance.user_id)
    expected_yesterday_energys["date"] = updater_instance.date
    updater_instance.db.insert_doc.assert_called_once_with(
        "Energys", expected_yesterday_energys
    )
