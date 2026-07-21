# Finance Dataset

Place a real Kaggle finance/P&L-style CSV in this folder (e.g. `finance.csv`). Nothing
else needs to change to start using it — `FinanceDataLoader`
(`backend/app/finance/data_loader.py`) auto-detects columns by alias, cleans the data,
and hands a canonical DataFrame to `FinanceAnalyticsService`.

## Suggested datasets

Any Kaggle "company financials / P&L / revenue-and-expenses" dataset with roughly
these fields works out of the box, e.g.:
- "Company Financials Dataset"
- "Business Profit and Loss Statements"
- "Startup/SME Revenue & Expenses" datasets

## Expected columns (any of these header spellings are recognized)

| Canonical field | Required? | Recognized header aliases (case/spacing insensitive) |
|---|---|---|
| `date`      | **Yes** | `date`, `transaction_date`, `period`, `month`, `posting_date` |
| `revenue`   | Need at least 2 of revenue/expenses/profit | `revenue`, `sales`, `income`, `total_revenue` |
| `expenses`  | Need at least 2 of revenue/expenses/profit | `expenses`, `expense`, `cost`, `total_expenses`, `cogs` |
| `profit`    | Need at least 2 of revenue/expenses/profit | `profit`, `net_profit`, `net_income`, `earnings` |
| `category`  | No | `category`, `expense_category`, `department` |
| `region`    | No | `region`, `state`, `area`, `territory` |

Whichever one of `revenue` / `expenses` / `profit` is missing is derived automatically
from the other two (`profit = revenue - expenses`, etc.). At least two of the three must
be present in the dataset.

## Adding a new/different dataset

1. Drop the CSV file into this folder. Multiple CSVs are supported — they're concatenated.
2. If the dataset's headers aren't already covered above, add the raw header name to the
   matching list in `COLUMN_ALIASES` inside `backend/app/finance/data_loader.py`. No other
   code changes are needed — `FinanceAnalyticsService`, the query mapper, and `FinanceAgent`
   all work off the canonical schema, not raw headers.
3. Rows with an unparseable date or non-numeric money columns are dropped automatically
   (reported via `EmptyDatasetError` if that leaves nothing usable).

Do not commit real datasets with sensitive data to source control if this repo is public.
