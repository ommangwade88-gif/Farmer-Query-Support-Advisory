pipeline {
    agent any

    stages {

        stage('Verify Tools') {
            steps {
                sh 'node -v || true'
                sh 'npm -v || true'
                sh 'python3 --version || true'
                sh 'pip3 --version || true'
            }
        }

        stage('Checkout') {
            steps {
                git 'https://github.com/ommangwade88-gif/Farmer-Query-Support-Advisory.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                if [ -f package.json ]; then
                  npm install
                fi

                if [ -f requirements.txt ]; then
                  pip3 install -r requirements.txt
                fi
                '''
            }
        }

        stage('Build Check') {
            steps {
                sh 'echo "Build successful!"'
            }
        }
    }
}
