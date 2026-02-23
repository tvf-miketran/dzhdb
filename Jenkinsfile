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
                script {
                    docker.build("flask-api:${BUILD_NUMBER}")
                }
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                docker stop flask-api || true
                docker rm flask-api || true
                docker run -d -p 5000:5000 --name flask-api flask-api:${BUILD_NUMBER}
                '''
            }
        }
    }
}