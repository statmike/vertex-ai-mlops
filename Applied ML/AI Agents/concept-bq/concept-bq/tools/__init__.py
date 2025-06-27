from .bq_query_hurricanes_per_year import bq_query_hurricanes_per_year
from .bq_query_hurricanes_per_year_filter import bq_query_hurricanes_per_year_filter

BQ_QUERY_TOOLS = [
    bq_query_hurricanes_per_year,
    bq_query_hurricanes_per_year_filter,
]