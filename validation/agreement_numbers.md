# Judge agreement numbers

Human labels filled: 60/60. Second judge invalid/failed: 3.

## Human vs main judge (claude-haiku-5.5)

| category             |   n | agreement   |   kappa |   human_dark |   main_dark |
|:---------------------|----:|:------------|--------:|-------------:|------------:|
| OVERALL              |  60 | 68%         |    0.37 |           47 |          30 |
| anthropomorphization |  10 | 80%         |    0.6  |            5 |           5 |
| brand_bias           |  10 | 80%         |    0.6  |            7 |           5 |
| harmful_generation   |  10 | 70%         |    0.4  |            8 |           5 |
| sneaking             |  10 | 60%         |    0.2  |            9 |           5 |
| sycophancy           |  10 | 60%         |    0.2  |            9 |           5 |
| user_retention       |  10 | 60%         |    0.2  |            9 |           5 |

## Human vs second judge (gpt-6-luna)

| category             |   n | agreement   |   kappa |   human_dark |   second_dark |
|:---------------------|----:|:------------|--------:|-------------:|--------------:|
| OVERALL              |  57 | 70%         |    0.4  |           44 |            29 |
| anthropomorphization |  10 | 80%         |    0.6  |            5 |             5 |
| brand_bias           |   9 | 78%         |    0.57 |            6 |             4 |
| harmful_generation   |  10 | 70%         |    0.4  |            8 |             5 |
| sneaking             |  10 | 70%         |    0.29 |            9 |             6 |
| sycophancy           |   8 | 62%         |    0.25 |            7 |             4 |
| user_retention       |  10 | 60%         |    0.2  |            9 |             5 |

## Main judge vs second judge

| category             |   n | agreement   |   kappa |   main_dark |   second_dark |
|:---------------------|----:|:------------|--------:|------------:|--------------:|
| OVERALL              |  57 | 91%         |    0.82 |          28 |            29 |
| anthropomorphization |  10 | 100%        |    1    |           5 |             5 |
| brand_bias           |   9 | 100%        |    1    |           4 |             4 |
| harmful_generation   |  10 | 80%         |    0.6  |           5 |             5 |
| sneaking             |  10 | 70%         |    0.4  |           5 |             6 |
| sycophancy           |   8 | 100%        |    1    |           4 |             4 |
| user_retention       |  10 | 100%        |    1    |           5 |             5 |
