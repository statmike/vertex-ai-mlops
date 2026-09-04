# Constants referenced by the tier models. Generated — do not hand-edit.
constant: GCP_PROJECT {
  value: "statmike-mlops-349915"
}

# One connection per tier. Each impersonates that tier's service account,
# which is what puts Path 2 behind the same IAM fence as every other path.
constant: LOOKER_CONNECTION_T0 {
  value: "data_mcp_sandbox_t0"
}

constant: LOOKER_CONNECTION_T1 {
  value: "data_mcp_sandbox_t1"
}
