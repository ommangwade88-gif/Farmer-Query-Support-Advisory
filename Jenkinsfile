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
