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
                    echo "=== Node Version ==="
                    node --version
                    npm --version
                    npm install
                    echo "=== Node install OK ==="
                '''
            }
        }

        stage('Install Python Dependencies') {
            steps {
                dir('python-service') {
                    sh '''
                        echo "=== Python Version ==="
                        python3 --version
                        pip3 install --no-cache-dir -r requirements.txt --break-system-packages
                        python3 -c "import flask, PIL, httpx; print('Python deps OK')"
                        echo "=== Python install OK ==="
                    '''
                }
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

                    echo "=== Built Images ==="
                    docker images | grep farmer
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

                        echo "=== Push complete ==="
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    echo "=== Deploy ==="
                    docker compose down --remove-orphans || true
                    docker compose up -d --build
                    sleep 8
                    docker compose ps
                    echo "=== App live at http://localhost:3000 ==="
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
