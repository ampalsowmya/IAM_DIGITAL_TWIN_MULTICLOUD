# Secrets Management Guide
===========================

This document describes how secrets are managed in the Multi-Cloud IAM Digital Twin system.

## Principles

1. **Never commit secrets to version control**
2. **Use environment variables for configuration**
3. **Use cloud-native secrets management in production**
4. **Rotate secrets regularly**
5. **Use least-privilege access to secrets**

## Secrets Required

### Neo4j
- `NEO4J_URI`: Neo4j connection URI
- `NEO4J_USER`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password

### AWS
- `AWS_ACCESS_KEY_ID`: AWS access key (or use IAM role)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key (or use IAM role)
- `AWS_REGION`: AWS region

### Azure AD
- `AZURE_TENANT_ID`: Azure AD tenant ID
- `AZURE_CLIENT_ID`: Azure AD app registration client ID
- `AZURE_CLIENT_SECRET`: Azure AD app registration client secret

### LLM (Azure OpenAI)
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Deployment name

### LLM (AWS Bedrock)
- `AWS_BEDROCK_REGION`: AWS Bedrock region
- `AWS_BEDROCK_MODEL_ID`: Model ID (uses AWS credentials)

## Development Environment

### Using .env file

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your secrets in `.env`:
   ```bash
   NEO4J_PASSWORD=your_actual_password
   AWS_ACCESS_KEY_ID=your_aws_key
   # ... etc
   ```

3. Ensure `.env` is in `.gitignore`:
   ```
   .env
   .env.local
   ```

### Loading Environment Variables

The application uses `pydantic-settings` to load environment variables from `.env` file automatically.

## Production Environment

### AWS Secrets Manager

For AWS deployments, use AWS Secrets Manager:

```python
import boto3
import json

def get_secret(secret_name: str) -> dict:
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
secrets = get_secret('multi-cloud-iam-digital-twin/secrets')
neo4j_password = secrets['neo4j_password']
```

**Setting up AWS Secrets Manager:**

1. Create secret in AWS Secrets Manager:
   ```bash
   aws secretsmanager create-secret \
     --name multi-cloud-iam-digital-twin/secrets \
     --secret-string file://secrets.json
   ```

2. Grant IAM permissions:
   ```json
   {
     "Effect": "Allow",
     "Action": [
       "secretsmanager:GetSecretValue",
       "secretsmanager:DescribeSecret"
     ],
     "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT:secret:multi-cloud-iam-digital-twin/*"
   }
   ```

### Azure Key Vault

For Azure deployments, use Azure Key Vault:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

def get_azure_secret(vault_url: str, secret_name: str) -> str:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    secret = client.get_secret(secret_name)
    return secret.value

# Usage
vault_url = "https://your-keyvault.vault.azure.net/"
neo4j_password = get_azure_secret(vault_url, "neo4j-password")
```

**Setting up Azure Key Vault:**

1. Create Key Vault:
   ```bash
   az keyvault create --name your-keyvault --resource-group your-rg --location eastus
   ```

2. Add secrets:
   ```bash
   az keyvault secret set --vault-name your-keyvault --name neo4j-password --value "your-password"
   ```

3. Grant access:
   ```bash
   az keyvault set-policy --name your-keyvault --upn user@domain.com --secret-permissions get list
   ```

### GCP Secret Manager

For GCP deployments, use GCP Secret Manager:

```python
from google.cloud import secretmanager

def get_gcp_secret(project_id: str, secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Usage
neo4j_password = get_gcp_secret("your-project-id", "neo4j-password")
```

## CI/CD Secrets

### GitHub Actions

Store secrets in GitHub repository settings:
- Settings → Secrets and variables → Actions → New repository secret

Required secrets:
- `NEO4J_PASSWORD`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AZURE_CLIENT_SECRET`
- `AZURE_OPENAI_API_KEY`
- `SONAR_TOKEN`
- `CODECOV_TOKEN`

### GitLab CI

Store secrets in GitLab CI/CD variables:
- Settings → CI/CD → Variables

Use masked and protected variables for sensitive data.

## Best Practices

1. **Rotate secrets regularly**: Set up automated rotation for production secrets
2. **Use separate secrets per environment**: dev, staging, production
3. **Audit secret access**: Log who accesses secrets and when
4. **Use short-lived credentials**: Prefer IAM roles over long-lived access keys
5. **Encrypt secrets at rest**: Ensure secrets are encrypted in storage
6. **Limit secret scope**: Only grant access to secrets needed for specific services
7. **Monitor secret usage**: Alert on unusual access patterns

## Security Scanning

The CI/CD pipeline includes:
- **TruffleHog**: Scans for committed secrets
- **Bandit**: Python security linter
- **SonarQube**: Static code analysis

## Emergency Procedures

If secrets are compromised:

1. **Immediately rotate the compromised secret**
2. **Revoke access** for the compromised credential
3. **Review access logs** to identify unauthorized usage
4. **Notify security team** and stakeholders
5. **Update incident response documentation**

## References

- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
- [Azure Key Vault Best Practices](https://docs.microsoft.com/en-us/azure/key-vault/general/best-practices)
- [GCP Secret Manager Best Practices](https://cloud.google.com/secret-manager/docs/best-practices)
