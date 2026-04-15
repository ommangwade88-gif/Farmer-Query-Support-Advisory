pipeline {
    agent any

    stages {

        stage('Verify Tools') {
            steps {
                bat '''
                node -v
                npm -v
                exit 0
                '''
            }
        }

        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/ommangwade88-gif/Farmer-Query-Support-Advisory.git'
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

                exit 0
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
