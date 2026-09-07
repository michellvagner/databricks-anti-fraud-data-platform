from pyspark.sql.functions import col, current_timestamp

df = (
    spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .option("sep", ";")
        .option(
            "cloudFiles.schemaLocation",
            "/Volumes/workspace/bronze/schema/transactions"
        )
        .load("/Volumes/workspace/bronze/landing/")
)

df_bronze = (
    df.select(
        "*",
        col("_metadata.file_name").alias("SOURCE_FILENAME"),
        col("_metadata.file_path").alias("SOURCE_FILE_PATH"),
        current_timestamp().alias("INGESTION_TS")
    )
)

query = (
    df_bronze.writeStream
        .format("delta")
        .outputMode("append")
        .option(
            "checkpointLocation",
            "/Volumes/workspace/bronze/checkpoints/transactions"
        )
        .trigger(availableNow=True)
        .toTable("workspace.bronze.transactions")
)

query.awaitTermination()