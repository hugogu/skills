# CI/CD Integration Examples

This document provides ready-to-use CI/CD configurations for integrating k6 load tests into your deployment pipeline.

## Table of Contents

- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Jenkins](#jenkins)
- [Azure DevOps](#azure-devops)
- [CircleCI](#circleci)

## GitHub Actions

Create `.github/workflows/performance.yml`:

```yaml
name: Performance Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run nightly at 2 AM
    - cron: '0 2 * * *'

jobs:
  load-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Start services
      run: |
        cp .env.example .env
        echo "TARGET_URL=${{ secrets.API_URL || 'https://test.k6.io' }}" >> .env
        docker-compose up -d influxdb grafana
        sleep 30
    
    - name: Run load test
      run: |
        docker-compose run --rm k6 run /scripts/templates/load-test-template.js
    
    - name: Upload results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: grafana-dashboard
        path: grafana/
    
    - name: Cleanup
      if: always()
      run: docker-compose down -v
```

## GitLab CI

Create `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - performance

variables:
  TARGET_URL: "${API_URL}"
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: ""

load_test:
  stage: performance
  image: docker:20.10.16
  services:
    - docker:20.10.16-dind
  before_script:
    - apk add --no-cache docker-compose
    - cp .env.example .env
    - echo "TARGET_URL=${TARGET_URL}" >> .env
    - docker-compose up -d influxdb grafana
    - sleep 30
  script:
    - docker-compose run --rm k6 run /scripts/templates/load-test-template.js
  after_script:
    - docker-compose down -v
  only:
    - merge_requests
    - main
```

## Jenkins

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any
    
    environment {
        TARGET_URL = credentials('api-url')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'cp .env.example .env'
                sh 'echo "TARGET_URL=${TARGET_URL}" >> .env'
                sh 'docker-compose up -d influxdb grafana'
                sh 'sleep 30'
            }
        }
        
        stage('Load Test') {
            steps {
                sh 'docker-compose run --rm k6 run /scripts/templates/load-test-template.js'
            }
        }
    }
    
    post {
        always {
            sh 'docker-compose down -v'
        }
        failure {
            mail to: 'team@example.com',
                 subject: "Performance Test Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}"
        }
    }
}
```

## Azure DevOps

Create `azure-pipelines.yml`:

```yaml
trigger:
  - main
  - develop

pr:
  - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: DockerCompose@0
  displayName: 'Start Services'
  inputs:
    containerregistrytype: 'Container Registry'
    dockerComposeFile: '**/docker-compose.yml'
    action: 'Run services'
    services: 'influxdb grafana'

- script: |
    cp .env.example .env
    echo "TARGET_URL=$(API_URL)" >> .env
    sleep 30
  displayName: 'Configure Environment'

- script: |
    docker-compose run --rm k6 run /scripts/templates/load-test-template.js
  displayName: 'Run Load Test'
  continueOnError: true

- task: DockerCompose@0
  displayName: 'Cleanup'
  condition: always()
  inputs:
    containerregistrytype: 'Container Registry'
    dockerComposeFile: '**/docker-compose.yml'
    action: 'Run a docker compose command'
    dockerComposeCommand: 'down -v'
```

## CircleCI

Create `.circleci/config.yml`:

```yaml
version: 2.1

jobs:
  load-test:
    docker:
      - image: cimg/base:stable
    steps:
      - setup_remote_docker:
          version: 20.10.18
      
      - checkout
      
      - run:
          name: Setup Environment
          command: |
            cp .env.example .env
            echo "TARGET_URL=${API_URL}" >> .env
      
      - run:
          name: Start Services
          command: |
            docker-compose up -d influxdb grafana
            sleep 30
      
      - run:
          name: Run Load Test
          command: |
            docker-compose run --rm k6 run /scripts/templates/load-test-template.js
      
      - run:
          name: Cleanup
          command: docker-compose down -v
          when: always

workflows:
  performance:
    jobs:
      - load-test:
          filters:
            branches:
              only:
                - main
                - develop
```

## Best Practices

1. **Run on schedule**: Run nightly tests to catch performance regressions
2. **Use secrets**: Store API URLs and credentials in CI secrets
3. **Set thresholds**: Define pass/fail criteria in test scripts
4. **Notifications**: Alert team when tests fail
5. **Artifacts**: Save Grafana dashboards and logs for analysis
6. **Parallel execution**: Run different test types in parallel
7. **Staging first**: Test against staging before production
