from pyspark.sql.functions import (
    col,
    count,
    sum,
    when,
    avg,
    round,
    date_format,
    coalesce,
    lit
)

df_gold = (
    spark.read.table("workspace.silver.transactions")
    .groupBy(
        "BANK",
        date_format(col("TRN_DT"), "yyyy-MM").alias("TRN_DT")
    )
    .agg(
        count("*").alias("QTY"),

        sum(
            when(
                (col("TRANSACTION_TYPE") == "A") &
                (col("REASON_CODE") == "000"),
                1
            ).otherwise(0)
        ).alias("QTY_APPROVED"),

        (
            sum(
                when(
                    (col("TRANSACTION_TYPE") == "A") &
                    (col("REASON_CODE") == "000"),
                    1
                ).otherwise(0)
            ) / count("*")
        ).alias("APPROVED_RATE"),

        sum("TRANSACTION_AMOUNT").alias("TRANSACTION_AMOUNT"),

        sum(
            when(
                (col("TRANSACTION_TYPE") == "A") &
                (col("REASON_CODE") == "000"),
                col("TRANSACTION_AMOUNT")
            ).otherwise(0)
        ).alias("TRANSACTION_AMOUNT_APPROVED"),

        (
            sum(
                when(
                    (col("TRANSACTION_TYPE") == "A") &
                    (col("REASON_CODE") == "000"),
                    col("TRANSACTION_AMOUNT")
                ).otherwise(0)
            )
            -
            sum(
                when(
                    (col("TRANSACTION_TYPE") == "O") &
                    (col("REASON_CODE") == "000"),
                    col("TRANSACTION_AMOUNT")
                ).otherwise(0)
            )
        ).alias("FATURAMENTO"),

        round(avg("TRANSACTION_AMOUNT"), 2).alias("TICKET_MEDIO"),

        round(
            avg(
                when(
                    (col("TRANSACTION_TYPE") == "A") &
                    (col("REASON_CODE") == "000"),
                    col("TRANSACTION_AMOUNT")
                ).otherwise(0)
            ),
            2
        ).alias("TICKET_MEDIO_APPROVED")
    )
)

query = (
    df_gold.write
        .format("delta")
        .mode("overwrite")
        .saveAsTable("workspace.gold.transactions")
)