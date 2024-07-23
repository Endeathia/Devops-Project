pipeline {
    agent any

    environment {
        AWS_REGION = 'us-east-1'
        CLUSTER_NAME = 'Atech'
        SCANNER_HOME = tool 'sonar-scanner'
    }

    stages {
        stage('Fetch Source Code') {
            steps {
                git branch: 'main', credentialsId: 'GitHubJuly', url: 'https://github.com/Endeathia/Devops-Project.git'
            }
        }

        stage('SonarQube Scan') {
            steps {
                script {
                    println("=====================================${STAGE_NAME}=====================================")
                    withSonarQubeEnv('sonar-server') {
                    withCredentials([string(credentialsId: 'sonar1907', variable: 'SONAR_TOKEN')]) {
                        sh "${SCANNER_HOME}/bin/sonar-scanner \
                        -Dsonar.projectKey=telegram\
                        -Dsonar.sources=./ \
                        -Dsonar.host.url=https://sonarqube.atech-bot.click/ \
                        -Dsonar.login=${SONAR_TOKEN}"
                    }
                }
            }
        }
        }

        stage('Quality gate'){
            steps {
                waitForQualityGate abortPipeline: true
            }
        }
    
        
        stage('Update kubeconfig') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                    sh '''
                    aws eks update-kubeconfig --region ${AWS_REGION} --name ${CLUSTER_NAME}
                    '''
                }
            }
        }
        
        stage('Update Namespace') {
            steps {
                sh 'kubectl config set-context --current --namespace=tamer'
            }
        }
    

        stage('Helm Install/Upgrade Polybot') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                    sh '''
                    export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
                    export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
                    helm upgrade polybot Kubernetes/polybot -f Kubernetes/polybot/values.yaml
                    '''
                }
            }
        }

        stage('Helm Install/Upgrade YOLOv5') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
                    sh '''
                    export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
                    export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
                    helm upgrade yolo5 Kubernetes/yolo5 -f Kubernetes/yolo5/values.yaml
                    '''
                }
            }
        }
    }
    
post {
    always {
        script {
            def jobName = env.JOB_NAME
            def buildNumber = env.BUILD_NUMBER
            def pipelineStatus = currentBuild.result ?: 'UNKNOWN'
            def bannerColor = pipelineStatus.toUpperCase() == 'SUCCESS' ? 'green' : 'red'

            def body = """
            <html>
            <body>
                <div style="border: 4px solid ${bannerColor}; padding: 10px;">
                    <h2>${jobName} - Build ${buildNumber}</h2>
                </div>
                <div style="background-color: ${bannerColor}; padding: 10px;">
                    <h3 style="color: white;">Pipeline Status: ${pipelineStatus.toUpperCase()}</h3>
                </div>
                <p>Check the <a href="${BUILD_URL}">console output</a>.</p>
            </body>
            </html>
            """

            emailext (
                subject: "${jobName} - Build ${buildNumber} - ${pipelineStatus.toUpperCase()}",
                body: body,
                to: 'tamerjjeney279@gmail.com',
                from: 'jenkins@example.com',
                replyTo: 'jenkins@example.com',
                mimeType: 'text/html',
            )
        }
    }
}
}

