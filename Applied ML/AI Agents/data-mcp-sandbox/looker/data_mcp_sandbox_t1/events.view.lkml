view: events {
  sql_table_name: `@{GCP_PROJECT}.data_mcp_sandbox_t1.raw_events_2026` ;;
  # Raw clickstream events. Used to determine whether a user is genuinely active.

  dimension: event_id {
    type: string
    primary_key: yes
    description: "Unique event identifier."
    sql: ${TABLE}.event_id ;;
  }

  dimension: user_id {
    type: string
    description: "References users.user_id."
    sql: ${TABLE}.user_id ;;
  }

  dimension: event_type {
    type: string
    description: "One of: page_view, click, add_to_cart, search."
    sql: ${TABLE}.event_type ;;
  }

  dimension_group: event {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    datatype: timestamp
    description: "When the event occurred."
    sql: ${TABLE}.event_ts ;;
  }


}