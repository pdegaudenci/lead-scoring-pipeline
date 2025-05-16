import snowflake.connector

conn = snowflake.connector.connect(
    user='TU_USUARIO',
    password='TU_PASSWORD',
    account='TU_ACCOUNT',
    warehouse='TU_WAREHOUSE',
    database='TU_DATABASE',
    schema='TU_SCHEMA'
)

cs = conn.cursor()
try:
    cs.execute("PUT file://path_local/dataset.csv @%lead_data")
    cs.execute("COPY INTO lead_data FROM @%lead_data FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY='\"')")
finally:
    cs.close()
conn.close()
