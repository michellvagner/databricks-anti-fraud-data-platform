from pyspark.sql.functions import col, regexp_replace, to_timestamp
from pyspark.sql.types import DecimalType


df_silver = (
    spark.read.table("workspace.bronze.transactions")
    .select(
        "TRANSACTION_ID",
        "BANK",
        "CARD_NUMBER",

        to_timestamp(
            regexp_replace(
                col("TRN_DT"),
                r"^(\d{4}-\d{2}-\d{2}) (\d{2})(\d{2}):",
                r"$1 $2:$3:"
            )
        ).alias("TRN_DT"),

        "TRANSACTION_TYPE",

        col("TRANSACTION_AMOUNT").cast(DecimalType(18, 2)).alias("TRANSACTION_AMOUNT"),
        col("CARD_LIMIT_TOTAL").cast(DecimalType(18, 2)).alias("CARD_LIMIT_TOTAL"),
        col("CARD_LIMIT_REMAINING").cast(DecimalType(18, 2)).alias("CARD_LIMIT_REMAINING"),
        
        "REASON_CODE",
        "POS_NUMBER",
        "MERCHANT_CATEGORY_CODE",
        "CURRENCY_CD",
        "TRANSACTION_COUNTRY_CD",
        "MERCHANT_ID",
        "MERCHANT_NAME",
        "MERCHANT_STATE",
        "MERCHANT_CITY",
        "AUTHORIZATION_CODE",
        "ACQUIRER_ID",
        "CARD_BRAND",

        col("RISK_SCORE").cast("int").alias("RISK_SCORE"),

        "BLOCK_IND",
        "SOURCE_FILENAME",
        "SOURCE_FILE_PATH",
        "INGESTION_TS"
    )
)

query = (
    df_silver.write
        .format("delta")
        .mode("overwrite")
        .saveAsTable("workspace.silver.transactions")
)