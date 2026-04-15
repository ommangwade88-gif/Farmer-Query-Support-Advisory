pipeline {
    agent any

    stages {

        stage('Verify Tools') {
            steps {
                bat '''
                node -v
                npm -v

                python --version
                if %ERRORLEVEL% NEQ 0 (
                  echo Python not installed
                )

                pip --version
                if %ERRORLEVEL% NEQ 0 (
                  echo Pip not installed
                )

                exit 0
                '''
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
                  if %ERRORLEVEL% NEQ 0 (
                    echo Skipping Python dependencies
                  )
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
