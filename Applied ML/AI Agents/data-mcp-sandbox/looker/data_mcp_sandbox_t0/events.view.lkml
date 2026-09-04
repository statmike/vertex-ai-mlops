view: events {
  sql_table_name: `@{GCP_PROJECT}.data_mcp_sandbox_t0.raw_events_2026` ;;

  dimension: event_id {
    type: string
    primary_key: yes
    sql: ${TABLE}.event_id ;;
  }

  dimension: user_id {
    type: string
    sql: ${TABLE}.user_id ;;
  }

  dimension: event_type {
    type: string
    sql: ${TABLE}.event_type ;;
  }

  dimension_group: event {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    datatype: timestamp
    sql: ${TABLE}.event_ts ;;
  }

}