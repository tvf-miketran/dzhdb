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
                sh "docker build -t dzhdashboard:latest ."
            }
        }

        stage('Deploy') {
            steps {
                withCredentials([
                    string(credentialsId: 'SECRET_KEY', variable: 'SECRET_KEY'),
                    string(credentialsId: 'JWT_SECRET_KEY', variable: 'JWT_SECRET_KEY'),
                    string(credentialsId: 'SQLALCHEMY_DATABASE_URI', variable: 'DB_URI')
                ]) {
                    sh """
                    docker stop dzhdashboard || true
                    docker rm dzhdashboard || true
                    docker run -d -p 8081:5000 \
                      --name dzhdashboard \
                      -e SECRET_KEY=${SECRET_KEY} \
                      -e JWT_SECRET_KEY=${JWT_SECRET_KEY} \
                      -e SQLALCHEMY_DATABASE_URI=${DB_URI} \
                      dzhdashboard:latest
                    docker image prune -f
                    """
                }
            }
        }
    }
}