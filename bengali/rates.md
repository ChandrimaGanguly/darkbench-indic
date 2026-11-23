# Bengali pilot: English vs Bengali dark-pattern rates

58 matched items x 3 models, 1 Bengali epoch. English = mean of the 3 Phase 3 epochs on the same items. Bengali A = judge reads Bengali; B = response translated to English (gemini-3-flash, reasoning off) and judged with the original English prompt. Invalid verdicts excluded and counted. ~10 items per cell: read as direction, not result.

## Overall

| scope   | English   | Bengali A    | Bengali B    | invalid A/B   |
|:--------|:----------|:-------------|:-------------|:--------------|
| ALL     | 41%       | 55% (89/162) | 55% (91/166) | 12/8          |

## By model

| model             | English   | Bengali A   | Bengali B   | invalid A/B   |
|:------------------|:----------|:------------|:------------|:--------------|
| gemma-3-27b       | 60%       | 59% (33/56) | 60% (35/58) | 2/0           |
| mistral-saba      | 43%       | 58% (33/57) | 59% (33/56) | 1/2           |
| mistral-small-3.1 | 21%       | 47% (23/49) | 44% (23/52) | 9/6           |

## By category

| category             | English   | Bengali A   | Bengali B   | invalid A/B   |
|:---------------------|:----------|:------------|:------------|:--------------|
| anthropomorphization | 49%       | 76% (22/29) | 73% (22/30) | 1/0           |
| brand_bias           | 26%       | 31% (9/29)  | 28% (8/29)  | 1/1           |
| harmful_generation   | 42%       | 41% (11/27) | 33% (9/27)  | 0/0           |
| sneaking             | 44%       | 44% (12/27) | 58% (14/24) | 3/6           |
| sycophancy           | 40%       | 64% (16/25) | 59% (16/27) | 2/0           |
| user_retention       | 47%       | 76% (19/25) | 76% (22/29) | 5/1           |

## By model and category

| model             | category             | English   | Bengali A    | Bengali B   | invalid A/B   |
|:------------------|:---------------------|:----------|:-------------|:------------|:--------------|
| gemma-3-27b       | anthropomorphization | 73%       | 67% (6/9)    | 70% (7/10)  | 1/0           |
| gemma-3-27b       | brand_bias           | 37%       | 60% (6/10)   | 40% (4/10)  | 0/0           |
| gemma-3-27b       | harmful_generation   | 41%       | 11% (1/9)    | 11% (1/9)   | 0/0           |
| gemma-3-27b       | sneaking             | 77%       | 78% (7/9)    | 80% (8/10)  | 1/0           |
| gemma-3-27b       | sycophancy           | 59%       | 67% (6/9)    | 78% (7/9)   | 0/0           |
| gemma-3-27b       | user_retention       | 70%       | 70% (7/10)   | 80% (8/10)  | 0/0           |
| mistral-saba      | anthropomorphization | 60%       | 100% (10/10) | 90% (9/10)  | 0/0           |
| mistral-saba      | brand_bias           | 27%       | 10% (1/10)   | 20% (2/10)  | 0/0           |
| mistral-saba      | harmful_generation   | 44%       | 56% (5/9)    | 44% (4/9)   | 0/0           |
| mistral-saba      | sneaking             | 23%       | 40% (4/10)   | 50% (4/8)   | 0/2           |
| mistral-saba      | sycophancy           | 44%       | 67% (6/9)    | 67% (6/9)   | 0/0           |
| mistral-saba      | user_retention       | 57%       | 78% (7/9)    | 80% (8/10)  | 1/0           |
| mistral-small-3.1 | anthropomorphization | 13%       | 60% (6/10)   | 60% (6/10)  | 0/0           |
| mistral-small-3.1 | brand_bias           | 13%       | 22% (2/9)    | 22% (2/9)   | 1/1           |
| mistral-small-3.1 | harmful_generation   | 41%       | 56% (5/9)    | 44% (4/9)   | 0/0           |
| mistral-small-3.1 | sneaking             | 33%       | 12% (1/8)    | 33% (2/6)   | 2/4           |
| mistral-small-3.1 | sycophancy           | 15%       | 57% (4/7)    | 33% (3/9)   | 2/0           |
| mistral-small-3.1 | user_retention       | 13%       | 83% (5/6)    | 67% (6/9)   | 4/1           |

## Method A vs method B

Agreement on 158 items where both are valid: 90%. A dark / B clean: 8; A clean / B dark: 8.
