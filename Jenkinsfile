pipeline {
    agent any

    environment {
        AWS_REGION = 'us-east-1'
        CLUSTER_NAME = 'Atech'
        SCANNER_HOME = tool 'sonar-scanner'
    }

    stages {
        stage('clean workspace') {
            steps {
                cleanWs()
            }
        }
        
        stage('Fetch Source Code') {
            steps {
                sh 'git clone https://github.com/Endeathia/Devops-Project.git'
            }
        }
        
        stage('Sonarqube Analysis') {
            steps {
                withSonarQubeEnv('sonar-server') {
                    sh '''$SCANNER_HOME/bin/sonar-scanner -Dsonar.projectName=MicroServiceApp \
                    -Dsonar.projectKey=MicroServiceApp'''
                }
            }
        }
        
        stage('Quality Gate') {
            steps {
                script {
                    waitForQualityGate abortPipeline: false, credentialsId: 'Sonar-token'
                }
            }
        }
        
        stage('Update kubeconfig') {
            steps {
                sh '''
                aws eks update-kubeconfig --region ${AWS_REGION} --name ${CLUSTER_NAME}
                '''
            }
        }
        
        stage('Update Namespace') {
            steps {
                sh 'kubectl config set-context --current --namespace=tamer-new'
            }
        }
    }
    
    post {
        always {
            echo 'Cleaning up...'
            cleanWs()
        }
        success {
            echo 'EKS cluster created and Helm chart deployed successfully!'
        }
        failure {
            echo 'Failed to create EKS cluster or deploy Helm chart.'
        }
    }
}
