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
                echo "Build #${env.BUILD_NUMBER} — workspace: ${env.WORKSPACE}"
                sh 'ls -la'
            }
        }

        stage('Install Node Dependencies') {
            steps {
                sh '''
                    echo "=== Node Install ==="
                    ls package.json
                    docker run --rm \
                      -v ${WORKSPACE}:/app \
                      -w /app \
                      node:18-alpine \
                      npm install --prefer-offline
                    echo "Node install OK"
                '''
            }
        }

        stage('Install Python Dependencies') {
            steps {
                sh '''
                    echo "=== Python Install ==="
                    ls python-service/requirements.txt
                    docker run --rm \
                      -v ${WORKSPACE}/python-service:/app \
                      -w /app \
                      python:3.10-slim \
                      pip install --no-cache-dir -r requirements.txt
                    echo "Python install OK"
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    echo "=== Docker Build ==="
                    docker build -t ${IMAGE_NODE}:${BUILD_NUMBER} -t ${IMAGE_NODE}:latest \
                      -f Dockerfile .

                    docker build -t ${IMAGE_PYTHON}:${BUILD_NUMBER} -t ${IMAGE_PYTHON}:latest \
                      -f python-service/Dockerfile ./python-service

                    echo "Built images:"
                    docker images | grep -E "farmer-node|farmer-python"
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
                        echo "=== Docker Push ==="
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin

                        docker tag ${IMAGE_NODE}:${BUILD_NUMBER}   $DOCKER_USER/${IMAGE_NODE}:${BUILD_NUMBER}
                        docker tag ${IMAGE_NODE}:latest            $DOCKER_USER/${IMAGE_NODE}:latest
                        docker tag ${IMAGE_PYTHON}:${BUILD_NUMBER} $DOCKER_USER/${IMAGE_PYTHON}:${BUILD_NUMBER}
                        docker tag ${IMAGE_PYTHON}:latest          $DOCKER_USER/${IMAGE_PYTHON}:latest

                        docker push $DOCKER_USER/${IMAGE_NODE}:${BUILD_NUMBER}
                        docker push $DOCKER_USER/${IMAGE_NODE}:latest
                        docker push $DOCKER_USER/${IMAGE_PYTHON}:${BUILD_NUMBER}
                        docker push $DOCKER_USER/${IMAGE_PYTHON}:latest

                        echo "Push complete"
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    echo "=== Deploy ==="
                    docker compose -f ${WORKSPACE}/docker-compose.yml down --remove-orphans || true
                    docker compose -f ${WORKSPACE}/docker-compose.yml up -d --build
                    sleep 8
                    docker compose -f ${WORKSPACE}/docker-compose.yml ps
                    echo "App live at http://localhost:3000"
                '''
            }
        }
    }

    post {
        success {
            echo "BUILD #${env.BUILD_NUMBER} SUCCESS — http://localhost:3000"
        }
        failure {
            echo "BUILD #${env.BUILD_NUMBER} FAILED — check Console Output above"
        }
        always {
            sh 'docker logout || true'
        }
    }
}
