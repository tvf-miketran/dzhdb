pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                docker build -t dzhdashboard:${BUILD_NUMBER} .
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                docker stop dzhdashboard || true
                docker rm dzhdashboard || true
                docker run -d -p 8081:8080 --name dzhdashboard dzhdashboard:${BUILD_NUMBER}
                '''
            }
        }
    }
}