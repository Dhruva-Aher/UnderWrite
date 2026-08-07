import json
import datahub.metadata.schema_classes as sc

model_urn = "urn:li:mlModel:(urn:li:dataPlatform:mlflow,churn_model_v2,PROD)"
dataset_urn = "urn:li:dataset:(urn:li:dataPlatform:snowflake,raw.customers,PROD)"

# Target Leakage Graph
target_leakage_aspects = {
    model_urn: {
        "MLModelPropertiesClass": sc.MLModelPropertiesClass(description="Churn Model").to_obj(),
        "UpstreamLineageClass": sc.UpstreamLineageClass(
            upstreams=[sc.UpstreamClass(dataset=dataset_urn, type=sc.DatasetLineageTypeClass.TRANSFORMED)]
        ).to_obj()
    },
    dataset_urn: {
        "DatasetPropertiesClass": sc.DatasetPropertiesClass(description="Raw Customers").to_obj(),
        "SchemaMetadataClass": sc.SchemaMetadataClass(
            schemaName="customers",
            platform="urn:li:dataPlatform:snowflake",
            version=1,
            hash="",
            platformSchema=sc.OtherSchemaClass(rawSchema=""),
            fields=[
                sc.SchemaFieldClass(fieldPath="id", type=sc.SchemaFieldDataTypeClass(type=sc.StringTypeClass()), nativeDataType="VARCHAR"),
                sc.SchemaFieldClass(fieldPath="customer_name", type=sc.SchemaFieldDataTypeClass(type=sc.StringTypeClass()), nativeDataType="VARCHAR"),
                sc.SchemaFieldClass(
                    fieldPath="customer_status", 
                    type=sc.SchemaFieldDataTypeClass(type=sc.StringTypeClass()), 
                    nativeDataType="VARCHAR",
                    globalTags=sc.GlobalTagsClass(tags=[sc.TagAssociationClass(tag="urn:li:tag:IS_TARGET")])
                ),
            ]
        ).to_obj()
    }
}

with open("demo/fixtures/target_leakage_metadata.json", "w") as f:
    json.dump(target_leakage_aspects, f, indent=2)

# Clean Graph (customer_status column removed)
clean_aspects = {
    model_urn: {
        "MLModelPropertiesClass": sc.MLModelPropertiesClass(description="Churn Model").to_obj(),
        "UpstreamLineageClass": sc.UpstreamLineageClass(
            upstreams=[sc.UpstreamClass(dataset=dataset_urn, type=sc.DatasetLineageTypeClass.TRANSFORMED)]
        ).to_obj()
    },
    dataset_urn: {
        "DatasetPropertiesClass": sc.DatasetPropertiesClass(description="Raw Customers").to_obj(),
        "SchemaMetadataClass": sc.SchemaMetadataClass(
            schemaName="customers",
            platform="urn:li:dataPlatform:snowflake",
            version=1,
            hash="",
            platformSchema=sc.OtherSchemaClass(rawSchema=""),
            fields=[
                sc.SchemaFieldClass(fieldPath="id", type=sc.SchemaFieldDataTypeClass(type=sc.StringTypeClass()), nativeDataType="VARCHAR"),
                sc.SchemaFieldClass(fieldPath="customer_name", type=sc.SchemaFieldDataTypeClass(type=sc.StringTypeClass()), nativeDataType="VARCHAR"),
            ]
        ).to_obj()
    }
}

with open("demo/fixtures/clean_metadata.json", "w") as f:
    json.dump(clean_aspects, f, indent=2)

print("Fixtures generated.")
