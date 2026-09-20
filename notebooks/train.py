from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = Path(__file__).resolve().parent / "dinosaurs.csv"
ARTIFACT_PATH = ROOT / "artifact" / "model.joblib"

FEATURES = ["dino_type", "length_m", "period", "lived_in"]
NUMERIC = ["length_m"]
CATEGORICAL = ["dino_type", "period", "lived_in"]
VALID_TYPES = {
    "sauropod",
    "large theropod",
    "small theropod",
    "euornithopod",
    "armoured dinosaur",
    "ceratopsian",
}


def load_frame(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["dino_type"] = df["type"].astype(str).str.strip()
    df["length_m"] = pd.to_numeric(
        df["length"].astype(str).str.replace("m", "", regex=False),
        errors="coerce",
    )
    df["period"] = df["period"].fillna("").str.split().str[:2].str.join(" ")
    df.loc[df["period"] == "", "period"] = None
    df["lived_in"] = df["lived_in"].replace("", pd.NA)
    df["carnivorous"] = (df["diet"].str.lower() == "carnivorous").astype(int)
    df = df.dropna(subset=["dino_type", "diet"])
    df = df[df["dino_type"].isin(VALID_TYPES)]
    df = df[df["period"].fillna("").str.contains("Triassic|Jurassic|Cretaceous", regex=True)]
    return df[FEATURES + ["carnivorous"]]


def build_pipeline() -> Pipeline:
    pre = ColumnTransformer(
        [
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                NUMERIC,
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("ohe", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                CATEGORICAL,
            ),
        ]
    )
    return Pipeline(
        [
            ("pre", pre),
            ("clf", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )


def main() -> None:
    df = load_frame(DATA_PATH)
    pipeline = build_pipeline()
    pipeline.fit(df[FEATURES], df["carnivorous"])
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": pipeline,
            "metadata": {
                "model_version": "1.0",
                "features": FEATURES,
                "threshold": 0.5,
                "task": "predict whether a dinosaur is carnivorous",
                "source": "Kaggle / NHM Jurassic Park exhaustive dinosaur dataset",
            },
        },
        ARTIFACT_PATH,
    )
    print(f"saved {ARTIFACT_PATH} rows={len(df)} carnivorous_share={df['carnivorous'].mean():.3f}")


if __name__ == "__main__":
    main()
