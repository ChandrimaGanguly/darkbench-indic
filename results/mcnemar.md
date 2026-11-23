# Mistral Small 3.1 vs Mistral Saba: paired test per category (English)

Each prompt is one pair; a model's verdict is its majority over 3 epochs (ties dropped). Exact McNemar on the discordant prompts. 110 prompts per category.

| category             |   prompts |   dropped |   Small dark |   Saba dark |   only Saba dark |   only Small dark | p      | p (Holm)   | direction    |
|:---------------------|----------:|----------:|-------------:|------------:|-----------------:|------------------:|:-------|:-----------|:-------------|
| anthropomorphization |       110 |         0 |           17 |          50 |               37 |                 4 | <0.001 | <0.001     | Saba higher  |
| brand_bias           |       109 |         1 |            2 |          21 |               21 |                 2 | <0.001 | <0.001     | Saba higher  |
| harmful_generation   |       106 |         4 |           39 |          39 |                6 |                 6 | 1.000  | 1.000      | equal        |
| sneaking             |       108 |         2 |           31 |          29 |               13 |                15 | 0.851  | 1.000      | Small higher |
| sycophancy           |       108 |         2 |           10 |          26 |               18 |                 2 | <0.001 | 0.001      | Saba higher  |
| user_retention       |       110 |         0 |           19 |          50 |               36 |                 5 | <0.001 | <0.001     | Saba higher  |

4 of 6 categories show a difference that survives a Holm correction at 0.05.
