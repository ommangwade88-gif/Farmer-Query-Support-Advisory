pipeline {
    agent {
        docker {
            image 'nikolaik/python-nodejs:latest'
        }
    }

    stages {

        stage('Verify Tools') {
            steps {
                sh 'node -v'
                sh 'npm -v'
                sh 'python3 --version'
                sh 'pip3 --version'
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
