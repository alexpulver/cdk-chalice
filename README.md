# cdk-chalice
**AWS CDK construct for AWS Chalice**

Packages AWS Chalice application into AWS SAM format and enriches the resulting
SAM template with additional configuration values. The construct currently 
supports only API handler Lambda functions. It is possible to specify
IAM role for API handler Lambda function or let `cdk-chalice` create one.
Additional environment variables can be passed to the application. 

#### AWS Chalice application requirements
It is recommended that AWS Chalice application will have a CDK-specific
stage with settings to be used by the accompanying CDK stack. 

Chalice application must have a `Dockerfile.cdk` file, that should package the 
application to `/chalice.out`. The last line should be:
```dockerfile
RUN chalice package --stage cdk /chalice.out
```
`cdk-chalice` will use `Dockerfile.cdk` to package the application in a clean environment
and retrieve the resulting `deployment.zip` and `sam.json` files for further
processing.
