view: users {
  sql_table_name: `@{GCP_PROJECT}.data_mcp_sandbox_t0.users` ;;

  dimension: user_id {
    type: string
    primary_key: yes
    sql: ${TABLE}.user_id ;;
  }

  dimension: is_active {
    type: yesno
    sql: ${TABLE}.is_active ;;
  }

  dimension_group: signup {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    datatype: date
    sql: ${TABLE}.signup_date ;;
  }

  dimension: region {
    type: string
    sql: ${TABLE}.region ;;
  }

}