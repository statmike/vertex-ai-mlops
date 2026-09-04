view: transactions {
  sql_table_name: `@{GCP_PROJECT}.data_mcp_sandbox_t0.transactions_v2_final` ;;

  dimension: txn_id {
    type: string
    primary_key: yes
    sql: ${TABLE}.txn_id ;;
  }

  dimension: user_id {
    type: string
    sql: ${TABLE}.user_id ;;
  }

  dimension: txn_amt_x2 {
    type: number
    sql: ${TABLE}.txn_amt_x2 ;;
  }

  dimension: revenue_amount {
    type: number
    sql: ${TABLE}.revenue_amount ;;
  }

  dimension: status_flg {
    type: yesno
    sql: ${TABLE}.status_flg ;;
  }

  dimension_group: txn {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    datatype: timestamp
    sql: ${TABLE}.txn_ts ;;
  }

}