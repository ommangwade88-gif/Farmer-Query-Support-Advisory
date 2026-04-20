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
            }
        }

        stage('Install Node Dependencies') {
            steps {
                sh '''
                    node --version && npm --version
                    npm install
                    echo "=== Node install OK ==="
                '''
            }
        }

        stage('Install Python Dependencies') {
            steps {
                dir('python-service') {
                    sh '''
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
                    docker build -t ${IMAGE_NODE}:${BUILD_NUMBER} -t ${IMAGE_NODE}:latest \
                        -f Dockerfile .

                    docker build -t ${IMAGE_PYTHON}:${BUILD_NUMBER} -t ${IMAGE_PYTHON}:latest \
                        -f python-service/Dockerfile ./python-service

                    echo "=== Built Images ==="
                    docker images | grep farmer
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    echo "=== Stopping old containers ==="
                    docker stop farmer-node farmer-python 2>/dev/null || true
                    docker rm   farmer-node farmer-python 2>/dev/null || true

                    echo "=== Starting Python service ==="
                    docker run -d \
                        --name farmer-python \
                        --restart unless-stopped \
                        -p 8000:8000 \
                        -e PORT=8000 \
                        ${IMAGE_PYTHON}:latest

                    echo "=== Waiting for Python to be ready ==="
                    sleep 8

                    echo "=== Starting Node service ==="
                    docker run -d \
                        --name farmer-node \
                        --restart unless-stopped \
                        -p 3000:3000 \
                        -e PORT=3000 \
                        -e PYTHON_SERVICE_URL=http://farmer-python:8000 \
                        --link farmer-python \
                        ${IMAGE_NODE}:latest

                    echo "=== Running Containers ==="
                    docker ps | grep farmer

                    echo "=== App live at http://localhost:3000 ==="
                '''
            }
        }
    }

    post {
        success {
            echo "BUILD #${env.BUILD_NUMBER} SUCCESS — open http://localhost:3000"
        }
        failure {
            echo "BUILD #${env.BUILD_NUMBER} FAILED — check Console Output above"
        }
    }
}
