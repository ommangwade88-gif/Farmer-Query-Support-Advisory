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
                echo "Branch: ${env.GIT_BRANCH} | Build: ${env.BUILD_NUMBER}"
            }
        }

        stage('Install Node Dependencies') {
            steps {
                sh '''
                    node -v && npm -v
                    npm install
                    echo "Node install OK"
                '''
            }
        }

        stage('Install Python Dependencies') {
            steps {
                dir('python-service') {
                    sh '''
                        pip3 install --no-cache-dir flask flask-cors pillow httpx gunicorn
                        python3 -c "import flask, PIL, httpx; print('Python deps OK')"
                    '''
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build -t ${IMAGE_NODE}:${BUILD_NUMBER}   -f Dockerfile .
                    docker build -t ${IMAGE_PYTHON}:${BUILD_NUMBER} -f python-service/Dockerfile ./python-service
                    echo "Docker images built successfully"
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
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker compose down --remove-orphans || true
                    docker compose up -d --build
                    echo "Waiting for services to start..."
                    sleep 10
                    docker compose ps
                '''
            }
        }
    }

    post {
        success {
            echo "Build #${env.BUILD_NUMBER} SUCCESS — App running at http://localhost:3000"
        }
        failure {
            echo "Build #${env.BUILD_NUMBER} FAILED — Check Console Output above"
        }
        always {
            sh 'docker logout || true'
        }
    }
}
