from app.services.fallback_generator import FallbackPipelineGenerator


def test_fallback_generator_preserves_requested_tools() -> None:
    description = (
        "I receive CSV files daily from an FTP server, store them in S3, "
        "transform with dbt, orchestrate with Dagster, and serve Snowflake."
    )

    spec = FallbackPipelineGenerator().generate(description)

    services = {service.name for service in spec.aws_services}
    assert "AWS Transfer Family" in services
    assert "dbt on AWS CodeBuild" in services
    assert "Dagster on Amazon ECS Fargate" in services
    assert spec.diagram.nodes
    assert spec.diagram.edges
