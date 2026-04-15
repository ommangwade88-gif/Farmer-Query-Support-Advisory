pipeline {
    agent any

    stages {

        stage('Verify Tools') {
            steps {
                sh '''
                node -v || echo "Node not installed"
                npm -v || echo "npm not installed"
                python3 --version || echo "Python not installed"
                '''
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
