pipeline {
    agent any

    environment {
        DOCKER_HUB_CREDS = credentials('dockerhub-credentials')
        IMAGE_NODE       = "farmer-node"
        IMAGE_PYTHON     = "farmer-python"
        IMAGE_TAG        = "${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install & Lint — Node') {
            agent {
                docker {
                    image 'node:18-alpine'
                    reuseNode true
                }
            }
            steps {
                sh '''
                    node -v && npm -v
                    npm install
                    node -e "require('./server.js')" &
                    sleep 2 && kill %1 || true
                '''
            }
        }

        stage('Install & Test — Python') {
            agent {
                docker {
                    image 'python:3.10-slim'
                    reuseNode true
                }
            }
            steps {
                dir('python-service') {
                    sh '''
                        pip install --no-cache-dir flask flask-cors pillow httpx gunicorn
                        python -c "import main; print('Python service import OK')"
                    '''
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build -t ${IMAGE_NODE}:${IMAGE_TAG}   -f Dockerfile .
                    docker build -t ${IMAGE_PYTHON}:${IMAGE_TAG} -f python-service/Dockerfile ./python-service
                '''
            }
        }

        stage('Docker Push') {
            steps {
                sh '''
                    echo "${DOCKER_HUB_CREDS_PSW}" | docker login -u "${DOCKER_HUB_CREDS_USR}" --password-stdin
                    docker tag ${IMAGE_NODE}:${IMAGE_TAG}   ${DOCKER_HUB_CREDS_USR}/${IMAGE_NODE}:${IMAGE_TAG}
                    docker tag ${IMAGE_PYTHON}:${IMAGE_TAG} ${DOCKER_HUB_CREDS_USR}/${IMAGE_PYTHON}:${IMAGE_TAG}
                    docker push ${DOCKER_HUB_CREDS_USR}/${IMAGE_NODE}:${IMAGE_TAG}
                    docker push ${DOCKER_HUB_CREDS_USR}/${IMAGE_PYTHON}:${IMAGE_TAG}
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker compose down --remove-orphans || true
                    IMAGE_TAG=${IMAGE_TAG} docker compose up -d --build
                '''
            }
        }
    }

    post {
        success {
            echo "Build #${env.BUILD_NUMBER} deployed successfully."
        }
        failure {
            echo "Build #${env.BUILD_NUMBER} failed."
        }
        always {
            sh 'docker logout || true'
        }
    }
}
