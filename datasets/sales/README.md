# Sales Dataset

Place a real Kaggle sales-transactions CSV in this folder (e.g. `sales.csv`). Nothing
else needs to change to start using it — `SalesDataLoader`
(`backend/app/sales/data_loader.py`) auto-detects columns by alias, cleans the data,
and hands a canonical DataFrame to `SalesAnalyticsService`.

## Suggested datasets

Any Kaggle "sales/superstore/retail transactions" dataset with roughly these fields
works out of the box, e.g.:
- "Superstore Sales Dataset"
- "Online Retail Dataset"
- "Sales Transactions from a Retail Business"

## Expected columns (any of these header spellings are recognized)

| Canonical field | Required? | Recognized header aliases (case/spacing insensitive) |
|---|---|---|
| `order_date`  | **Yes** | `order_date`, `order date`, `date`, `invoice_date` |
| `revenue`     | Yes, unless `quantity` + `unit_price` are both present | `revenue`, `sales`, `amount`, `total`, `total_amount`, `sale_amount` |
| `quantity`    | Only if no `revenue` column | `quantity`, `qty`, `units`, `order_quantity` |
| `unit_price`  | Only if no `revenue` column | `unit_price`, `price`, `unit_cost` |
| `order_id`    | No (falls back to row count) | `order_id`, `id`, `invoice_id`, `order_number` |
| `region`      | No (regional KPIs report "unavailable" if absent) | `region`, `state`, `area`, `territory` |
| `product`     | No | `product`, `product_name`, `item`, `category` |
| `customer`    | No | `customer`, `customer_name`, `client`, `client_name` |

## Adding a new/different dataset

1. Drop the CSV file into this folder. Multiple CSVs are supported — they're concatenated.
2. If the dataset's headers aren't already covered above, add the raw header name to the
   matching list in `COLUMN_ALIASES` inside `backend/app/sales/data_loader.py`. No other
   code changes are needed — `SalesAnalyticsService`, the query mapper, and `SalesAgent`
   all work off the canonical schema, not raw headers.
3. Rows with an unparseable date or no computable revenue are dropped automatically
   (reported via `EmptyDatasetError` if that leaves nothing usable).

Do not commit real datasets with sensitive data to source control if this repo is public.
