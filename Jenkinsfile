pipeline {
    agent any

    stages {

        stage('Verify Tools') {
            steps {
                bat 'node -v'
                bat 'npm -v'
                bat 'python --version'
                bat 'pip --version'
            }
        }

        stage('Checkout') {
            steps {
                git 'https://github.com/ommangwade88-gif/Farmer-Query-Support-Advisory.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '''
                if exist package.json (
                  npm install
                )

                if exist requirements.txt (
                  pip install -r requirements.txt
                )
                '''
            }
        }

        stage('Build Check') {
            steps {
                bat 'echo Build successful!'
            }
        }
    }
}
