## Table of contents
* [Introduction: Continuous Delployment and Integration for Data pipeline](#Introduction)
* [Technologies](#technologies)
* [Related Works](#related-works)

## Introduction: Continuous Delployment and Integration for Data pipeline
This projects covers the setup and integration of Airflow with dbt, with git changes continuously integrated, built and deployed to ECS containers hosted on Fargate (serverless) through AWS Codebuild, ECR and Codpipeline. EFS is used to maintain storage persistence, and an ELB to ensure static endpoint. <br />
### Note:
A more detailed post will be shared via Medium (with link here), explaining the required IAM accesses, roles and pictorial representions of the integration process.

## Technologies
The tools used 
1. Airflow
2. dbt
3. Git
4. Docker
5. Codebuild and associated buildspec
6. to host the imagedefinitions (output of the build stage, and the ENV file for the containers)
7. Elastic Container Registry to host the airflow image
8. Code Pipeline and associated Task definition
9. Elastic File System for Persistent storage
10. Elastic Load Balancer for static endpoint
11. Cloud watch for container log monitoring

## Related Works
1. Earlier works utilizing Jenkins for build, and EC2 for container hosting https://github.com/Ebuk-a/airflow-dbt-docker 
2. Future work: Deployment on EKS instead of ECS.

