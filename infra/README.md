# AWS configuration

Later steps will add ECS task definitions and IAM trust/permission policy templates here.
No cloud resources are provisioned during prerequisite setup.

Planned files include `ecs-task-definition.json`, `task-execution-trust.json`,
`github-oidc-trust.json` and `github-deploy-policy.json`. Add `task-policy.json`
only when the application actually requires an AWS task role.

Store AWS sign-in configuration and temporary credentials in the ignored `.aws/`
directory, using the PowerShell helpers. Do not put credentials in this directory.
