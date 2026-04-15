pipeline {
    agent none

    stages {

        stage('Node Build') {
            agent {
                docker { image 'node:18' }
            }
            steps {
                sh '''
                node -v
                npm -v

                if [ -f package.json ]; then
                  npm install
                fi
                '''
            }
        }

        stage('Python Check') {
            agent {
                docker { image 'python:3.10' }
            }
            steps {
                sh '''
                python --version

                if [ -f requirements.txt ]; then
                  pip install -r requirements.txt
                fi
                '''
            }
        }

        stage('Build Check') {
            agent any
            steps {
                echo 'Build successful!'
            }
        }
    }
}s
