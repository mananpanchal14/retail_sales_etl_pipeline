import pandas as pd
import numpy as np
from pathlib import Path

# - Path → telling Python where the project's data folder is located in a reliable way.

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = DATA_DIR / "processed"

orders = pd.read_csv(DATA_DIR / "olist_orders_dataset.csv")
order_items = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv")
payments = pd.read_csv(DATA_DIR / "olist_order_payments_dataset.csv")

orders["order_purchase_timestamp"] = pd.to_datetime(orders["order_purchase_timestamp"])
orders["order_delivered_customer_date"] = pd.to_datetime(orders["order_delivered_customer_date"])
orders["order_estimated_delivery_date"] = pd.to_datetime(orders["order_estimated_delivery_date"])

orders["delivery_delay_days"] = (orders["order_delivered_customer_date"] - orders["order_estimated_delivery_date"]).dt.days

orders["delivery_risk_level"] = np.select(
    [
        orders["delivery_delay_days"] <= 0,
        orders["delivery_delay_days"].between(1, 3),
        orders["delivery_delay_days"].between(4, 7),
        orders["delivery_delay_days"] >= 8
    ],
    [
        "Low",
        "Moderate",
        "High",
        "Very High"
    ],
    default="Unknown"
)

order_value = (order_items.groupby("order_id")
               .agg(total_product_value=("price", "sum"),total_freight_value=("freight_value", "sum")).reset_index())

print("Order-level value table:")
print("Rows:", len(order_value))
print("Unique orders:", order_value["order_id"].nunique())
print("Order IDs unique:", order_value["order_id"].is_unique)

orders = orders.merge(
    order_value[
        ["order_id", "total_product_value", "total_freight_value"]
    ],
    on="order_id",
    how="left"
)

print("Orders after order-value merge:")
print("Rows:", len(orders))
print("Unique orders:", orders["order_id"].nunique())
print("Order IDs unique:", orders["order_id"].is_unique)

payment_type_count = payments.groupby("order_id")["payment_type"].nunique().rename("payment_type_count")

single_payment_type = payments.groupby("order_id")["payment_type"].first().rename("payment_type")

order_payment_type = pd.concat(
    [single_payment_type, payment_type_count],
    axis=1
).reset_index()

order_payment_type.loc[
    order_payment_type["payment_type_count"] > 1,
    "payment_type"
] = "multiple"

order_payment_type = order_payment_type[
    ["order_id", "payment_type"]
]

print("Order-level payment table:")
print("Rows:", len(order_payment_type))
print("Unique orders:", order_payment_type["order_id"].nunique())
print("Order IDs unique:", order_payment_type["order_id"].is_unique)

orders = orders.merge(
    order_payment_type,
    on="order_id",
    how="left"
)

print("Orders after payment merge:")
print("Rows:", len(orders))
print("Unique orders:", orders["order_id"].nunique())
print("Order IDs unique:", orders["order_id"].is_unique)
print("Missing payment types:", orders["payment_type"].isna().sum())

print(orders.columns.tolist())

final_orders = orders[
    [
        "order_id",
        "customer_id",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "delivery_delay_days",
        "delivery_risk_level",
        "total_product_value",
        "total_freight_value",
        "payment_type"
    ]
].copy()

print("Final dataset:")
print("Shape:", final_orders.shape)
print("Unique orders:", final_orders["order_id"].nunique())
print("Order IDs unique:", final_orders["order_id"].is_unique)

expected_columns = [
    "order_id",
    "customer_id",
    "order_purchase_timestamp",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "delivery_delay_days",
    "delivery_risk_level",
    "total_product_value",
    "total_freight_value",
    "payment_type"
]

assert final_orders["order_id"].is_unique
assert final_orders.columns.tolist() == expected_columns
assert set(final_orders["delivery_risk_level"].unique()) <= {
    "Low",
    "Moderate",
    "High",
    "Very High",
    "Unknown"
}

print("\nMissing values:")
print(final_orders.isna().sum())

print("Delivery risk levels:")
print(final_orders["delivery_risk_level"].value_counts())

OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "final_orders.csv"

final_orders.to_csv(OUTPUT_FILE, index=False)

print(f"Final dataset saved to: {OUTPUT_FILE}")


'''
check_output = pd.read_csv(OUTPUT_FILE)

print("\nOutput file verification:")
print("Shape:", check_output.shape)
print("Unique orders:", check_output["order_id"].nunique())
print("Order IDs unique:", check_output["order_id"].is_unique)
print("Columns:", check_output.columns.tolist())
'''