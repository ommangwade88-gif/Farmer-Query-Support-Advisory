// Declarative pipeline for Jenkins (Linux agents with sh; Node 18+ and Python 3.10+ on PATH).
// Repo: https://github.com/ommangwade88-gif/Farmer-Query-Support-Advisory
pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    stages {
        stage('Install Node') {
            steps {
                sh 'node --version'
                sh 'npm ci'
            }
        }

        stage('Install Python') {
            steps {
                sh 'python3 --version'
                dir('python-service') {
                    sh 'python3 -m pip install --upgrade pip'
                    sh 'python3 -m pip install -r requirements.txt'
                }
            }
        }

        stage('Verify') {
            parallel {
                stage('Node syntax') {
                    steps {
                        sh 'node --check server.js'
                    }
                }
                stage('Python bytecode') {
                    steps {
                        sh 'python3 -m compileall -q python-service'
                    }
                }
            }
        }

        stage('Smoke: Flask health') {
            steps {
                dir('python-service') {
                    sh '''
                        set -e
                        nohup python3 main.py > flask-ci.log 2>&1 &
                        echo $! > flask-ci.pid
                        for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
                          if curl -sf http://127.0.0.1:8000/api/health; then
                            break
                          fi
                          sleep 2
                        done
                        curl -sf http://127.0.0.1:8000/api/health
                        kill "$(cat flask-ci.pid)" || true
                        wait "$(cat flask-ci.pid)" 2>/dev/null || true
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'CI finished successfully.'
        }
        failure {
            echo 'CI failed — check logs for Node/Python/smoke stages.'
        }
    }
}
