# CFPB complaint data: exploration report

Window for the feasibility check: 2023-01-01 to end; eligible = has text and 50-400 words.

## 1. Size and dates

- Rows: 16,558,052
- Dates: 2011-12-01 to 2026-07-06
- Complaint IDs: 16,555,611 present, 16,555,611 unique, 0 repeated (0.0%)

## 2. How many complaints have text (the model's input)

- With text: 3,815,251 of 16,558,052 (23.0%)
- Identical texts: 1,254,594 rows repeat an earlier text (32.9%)
- Texts containing XXXX masks: 2,576,329 (67.5%)

| year | rows | with_text | share_with_text |
| --- | --- | --- | --- |
| 2011 | 2,536 | 0 | 0.0% |
| 2012 | 72,368 | 0 | 0.0% |
| 2013 | 108,214 | 0 | 0.0% |
| 2014 | 152,909 | 0 | 0.0% |
| 2015 | 168,273 | 54,723 | 32.5% |
| 2016 | 191,294 | 77,766 | 40.7% |
| 2017 | 242,745 | 115,311 | 47.5% |
| 2018 | 257,132 | 118,393 | 46.0% |
| 2019 | 277,241 | 124,843 | 45.0% |
| 2020 | 444,214 | 174,298 | 39.2% |
| 2021 | 495,939 | 203,570 | 41.0% |
| 2022 | 800,255 | 337,280 | 42.1% |
| 2023 | 1,170,765 | 442,373 | 37.8% |
| 2024 | 2,734,276 | 814,385 | 29.8% |
| 2025 | 5,443,265 | 1,222,107 | 22.5% |
| 2026 | 3,875,331 | 85,162 | 2.2% |
| unknown | 121,295 | 45,040 | 37.1% |

## 3. Complaint length (words, complaints with text)

| words | complaints | share |
| --- | --- | --- |
| <20 | 156,574 | 4.1% |
| 20-49 | 558,730 | 14.6% |
| 50-99 | 910,699 | 23.9% |
| 100-199 | 1,134,984 | 29.7% |
| 200-399 | 732,395 | 19.2% |
| 400-799 | 254,584 | 6.7% |
| 800+ | 67,285 | 1.8% |

## 4. Product labels (complaints with text)

Look for near-duplicate names: the CFPB renamed several products over the years, so the same kind of complaint can carry different labels in different years.

| product | with_text | share | years_seen |
| --- | --- | --- | --- |
| Credit reporting or other personal consumer reports | 1,670,944 | 43.8% | 2023-2026 |
| Credit reporting, credit repair services, or other personal consumer reports | 807,500 | 21.2% | 2017-2023 |
| Debt collection | 434,150 | 11.4% | 2015-2026 |
| Checking or savings account | 182,763 | 4.8% | 2017-2026 |
| Mortgage | 144,808 | 3.8% | 2015-2026 |
| Credit card | 123,076 | 3.2% | 2015-2026 |
| Money transfer, virtual currency, or money service | 118,842 | 3.1% | 2017-2026 |
| Credit card or prepaid card | 108,683 | 2.8% | 2017-2023 |
| Student loan | 61,882 | 1.6% | 2015-2026 |
| Vehicle loan or lease | 51,951 | 1.4% | 2017-2026 |
| Credit reporting | 31,587 | 0.8% | 2015-2017 |
| Payday loan, title loan, personal loan, or advance loan | 17,353 | 0.5% | 2023-2026 |
| Payday loan, title loan, or personal loan | 17,226 | 0.5% | 2017-2023 |
| Bank account or service | 14,883 | 0.4% | 2015-2017 |
| Prepaid card | 11,318 | 0.3% | 2015-2026 |
| Consumer Loan | 9,458 | 0.2% | 2015-2017 |
| Debt or credit management | 5,277 | 0.1% | 2023-2026 |
| Payday loan | 1,745 | 0.0% | 2015-2017 |
| Money transfers | 1,497 | 0.0% | 2015-2017 |
| Other financial service | 292 | 0.0% | 2015-2017 |
| Virtual currency | 16 | 0.0% | 2015-2017 |

- Distinct issue labels: 173 across 21 products (full list in issues.csv)

## 5. Company response to consumer (complaints with text)

| response | with_text | share |
| --- | --- | --- |
| Closed with explanation | 2,530,898 | 66.3% |
| Closed with non-monetary relief | 1,172,149 | 30.7% |
| Closed with monetary relief | 96,526 | 2.5% |
| Untimely response | 10,828 | 0.3% |
| Closed | 3,741 | 0.1% |
| (missing) | 984 | 0.0% |
| In progress | 125 | 0.0% |

## 6. Feasibility for the POC

- Eligible complaints: 1,852,149 (after removing identical texts: about 1,113,201)

`top5_issue_share` = how much of each product the 5 most common issues cover. `enough_for_150`: yes = at least 450 eligible, tight = 150-449, no = under 150.

| product | eligible | share | top5_issue_share | enough_for_150 |
| --- | --- | --- | --- | --- |
| Credit reporting or other personal consumer reports | 1,188,884 | 64.2% | 99.5% | yes |
| Debt collection | 158,502 | 8.6% | 96.8% | yes |
| Credit reporting, credit repair services, or other personal consumer reports | 148,297 | 8.0% | 99.2% | yes |
| Checking or savings account | 92,802 | 5.0% | 99.5% | yes |
| Money transfer, virtual currency, or money service | 76,539 | 4.1% | 90.0% | yes |
| Credit card | 74,268 | 4.0% | 71.7% | yes |
| Mortgage | 31,632 | 1.7% | 98.0% | yes |
| Vehicle loan or lease | 22,026 | 1.2% | 89.9% | yes |
| Student loan | 21,191 | 1.1% | 96.6% | yes |
| Payday loan, title loan, personal loan, or advance loan | 13,121 | 0.7% | 66.7% | yes |
| Credit card or prepaid card | 12,004 | 0.6% | 66.3% | yes |
| Prepaid card | 7,686 | 0.4% | 99.6% | yes |
| Debt or credit management | 3,342 | 0.2% | 87.7% | yes |
| Payday loan, title loan, or personal loan | 1,855 | 0.1% | 67.4% | yes |

Read samples.csv (70 complaints) before trusting the labels.
