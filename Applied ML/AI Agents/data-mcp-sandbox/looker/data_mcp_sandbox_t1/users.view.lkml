view: users {
  sql_table_name: `@{GCP_PROJECT}.data_mcp_sandbox_t1.users` ;;
  # Registered users. The is_active flag is NOT the governed definition of Active.

  dimension: user_id {
    type: string
    primary_key: yes
    description: "Unique user identifier."
    sql: ${TABLE}.user_id ;;
  }

  dimension: is_active {
    type: yesno
    description: "Raw account-status flag. NOT the governed definition of an Active user — see the Active User business rule."
    sql: ${TABLE}.is_active ;;
  }

  dimension_group: signup {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    datatype: date
    description: "Date the user registered."
    sql: ${TABLE}.signup_date ;;
  }

  dimension: region {
    type: string
    description: "Sales region: North, South, East, or West."
    sql: ${TABLE}.region ;;
  }

  dimension: active_user_status {
    type: string
    description: "An Active User is a user whose is_active flag is TRUE AND who has at least one event in raw_events_2026 within the trailing 30 days. The is_active flag alone is NOT sufficient — roughly 20% of flagged users are dormant and must be excluded."
    sql: CASE WHEN ${TABLE}.is_active AND EXISTS (
           SELECT 1 FROM `@{GCP_PROJECT}.data_mcp_sandbox_t1.raw_events_2026` e
           WHERE e.user_id = ${TABLE}.user_id
             AND e.event_ts >= TIMESTAMP_SUB(
                   CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
         ) THEN 'Active' ELSE 'Inactive' END ;;
  }

}