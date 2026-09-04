connection: "@{LOOKER_CONNECTION_T0}"

include: "/data_mcp_sandbox_t0/*.view.lkml"

explore: transactions {
  label: "Transactions (tier 0)"
  join: users {
    type: left_outer
    relationship: many_to_one
    sql_on: ${transactions.user_id} = ${users.user_id} ;;
  }
  join: events {
    type: left_outer
    relationship: one_to_many
    sql_on: ${transactions.user_id} = ${events.user_id} ;;
  }
}
