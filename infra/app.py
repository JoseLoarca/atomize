#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.atomize_stack import AtomizeStack

app = cdk.App()
AtomizeStack(
    app,
    "AtomizeStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

app.synth()
