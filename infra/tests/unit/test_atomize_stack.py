import aws_cdk as core
import aws_cdk.assertions as assertions

from stacks.atomize_stack import AtomizeStack


def test_stack_synthesizes_core_resources():
    app = core.App()
    stack = AtomizeStack(app, "atomize-test")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::RDS::DBInstance", 1)
    template.resource_count_is("AWS::S3::Bucket", 1)
    template.resource_count_is("AWS::Cognito::UserPool", 1)
    template.resource_count_is("AWS::Lambda::Function", 2)
    template.resource_count_is("AWS::Events::Rule", 1)

    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "LifecycleConfiguration": {
                "Rules": assertions.Match.array_with(
                    [
                        assertions.Match.object_like(
                            {"ExpirationInDays": 180}
                        )
                    ]
                )
            }
        },
    )
