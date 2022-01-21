import pathlib
import pandas as pd
import concepts


context_df = pd.read_csv(
    pathlib.Path(__file__).parent / "data" / "kaggle_context.csv", index_col=0
)

attribute_counts = context_df.sum().sort_values(ascending=False)

dataset_df = pd.read_csv(
    pathlib.Path(__file__).parent / "data" / "kaggle.csv", index_col=0
)

context = concepts.Context.fromjson(
    pathlib.Path(__file__).parent / "data" / "lattice.json"
)

basic_levels = tuple(
    map(
        float,
        (pathlib.Path(__file__).parent / "data" / "basic_level.txt")
        .read_text()
        .split(","),
    )
)

min_extent_size = len(min(context.lattice, key=lambda c: len(c.extent)).extent)
max_extent_size = len(max(context.lattice, key=lambda c: len(c.extent)).extent)
