view: transactions {
  sql_table_name: `@{GCP_PROJECT}.data_mcp_sandbox_t1.transactions_v2_final` ;;
  # Transaction records. Net revenue lives in txn_amt_x2. The column named revenue_amount is gross list price, not revenue.

  dimension: txn_id {
    type: string
    primary_key: yes
    description: "Unique transaction identifier."
    sql: ${TABLE}.txn_id ;;
  }

  dimension: user_id {
    type: string
    description: "References users.user_id."
    sql: ${TABLE}.user_id ;;
  }

  dimension: txn_amt_x2 {
    type: number
    description: "Net revenue for the transaction. THIS is the revenue column. Nullable — a NULL means revenue was never recorded."
    sql: ${TABLE}.txn_amt_x2 ;;
  }

  dimension: revenue_amount {
    type: number
    description: "MISNAMED. Despite the name this is NOT revenue — it is the gross list price before discounts, kept from a legacy schema. Do not sum it to report revenue; use txn_amt_x2."
    sql: ${TABLE}.revenue_amount ;;
  }

  dimension: status_flg {
    type: yesno
    description: "Refund status. TRUE means the transaction was refunded. Refunded rows must be excluded from net revenue."
    sql: ${TABLE}.status_flg ;;
  }

  dimension_group: txn {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    datatype: timestamp
    description: "When the transaction occurred."
    sql: ${TABLE}.txn_ts ;;
  }

  measure: total_revenue {
    type: sum
    description: "Net Revenue is SUM(txn_amt_x2) over transactions_v2_final, and MUST exclude refunded transactions (status_flg = TRUE). Do not use revenue_amount — despite its name that column is gross list price before discounts. It overstates each transaction by roughly 25%, and far more in aggregate because a small number of revenue_amount rows carry data-quality outliers. NULL txn_amt_x2 means revenue was never recorded and is excluded from the sum."
    sql: ${txn_amt_x2} ;;
    filters: [status_flg: "no"]
    value_format_name: usd
  }

}