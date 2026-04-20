pipeline {
    agent any

    environment {
        IMAGE_NODE   = "farmer-node"
        IMAGE_PYTHON = "farmer-python"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                echo "Build #${env.BUILD_NUMBER} started"
            }
        }

        stage('Install Node Dependencies') {
            steps {
                sh '''
                    docker run --rm \
                      -v "$WORKSPACE":/app \
                      -w /app \
                      node:18-alpine \
                      sh -c "npm install && echo Node install OK"
                '''
            }
        }

        stage('Install Python Dependencies') {
            steps {
                sh '''
                    docker run --rm \
                      -v "$WORKSPACE/python-service":/app \
                      -w /app \
                      python:3.10-slim \
                      sh -c "pip install --no-cache-dir flask flask-cors pillow httpx gunicorn && python -c 'import flask, PIL, httpx; print(\"Python deps OK\")'"
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build -t ${IMAGE_NODE}:${BUILD_NUMBER}   -f Dockerfile .
                    docker build -t ${IMAGE_PYTHON}:${BUILD_NUMBER} -f python-service/Dockerfile ./python-service
                    echo "Images built: ${IMAGE_NODE}:${BUILD_NUMBER} and ${IMAGE_PYTHON}:${BUILD_NUMBER}"
                '''
            }
        }

        stage('Docker Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin

                        docker tag ${IMAGE_NODE}:${BUILD_NUMBER}   $DOCKER_USER/${IMAGE_NODE}:${BUILD_NUMBER}
                        docker tag ${IMAGE_NODE}:${BUILD_NUMBER}   $DOCKER_USER/${IMAGE_NODE}:latest
                        docker tag ${IMAGE_PYTHON}:${BUILD_NUMBER} $DOCKER_USER/${IMAGE_PYTHON}:${BUILD_NUMBER}
                        docker tag ${IMAGE_PYTHON}:${BUILD_NUMBER} $DOCKER_USER/${IMAGE_PYTHON}:latest

                        docker push $DOCKER_USER/${IMAGE_NODE}:${BUILD_NUMBER}
                        docker push $DOCKER_USER/${IMAGE_NODE}:latest
                        docker push $DOCKER_USER/${IMAGE_PYTHON}:${BUILD_NUMBER}
                        docker push $DOCKER_USER/${IMAGE_PYTHON}:latest

                        docker logout
                        echo "Images pushed to Docker Hub"
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker compose down --remove-orphans || true
                    docker compose up -d --build
                    sleep 10
                    docker compose ps
                    echo "App running at http://localhost:3000"
                '''
            }
        }
    }

    post {
        success {
            echo "Build #${env.BUILD_NUMBER} SUCCESS — http://localhost:3000"
        }
        failure {
            echo "Build #${env.BUILD_NUMBER} FAILED — check Console Output"
        }
        always {
            sh 'docker logout || true'
        }
    }
}
