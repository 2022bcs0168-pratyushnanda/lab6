pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        VENV_DIR = ".venv"
        DOCKER_IMAGE = "wine_predict_2022bcs0168"
        SHOULD_DEPLOY = "false"
        CUR_R2 = ""
        CUR_MSE = ""
    }

    stages {

        // -------------------------------
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // -------------------------------
        stage('Setup Python Virtual Environment') {
            steps {
                sh '''
                    set -euxo pipefail

                    # Install system dependencies (first time or if missing)
                    apt-get update
                    apt-get install -y \
                        python3 \
                        python3-venv \
                        python3-pip \
                        jq \
                        bc

                    # Create and activate virtual environment
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate

                    # Install Python dependencies
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        // -------------------------------
        stage('Train Model') {
            steps {
                sh '''
                    set -euxo pipefail
                    . ${VENV_DIR}/bin/activate
                    python src/train.py
                    test -f artifacts/metrics.json
                '''
            }
        }

        // -------------------------------
        stage('Read Accuracy') {
            steps {
                script {
                    env.CUR_MSE = sh(
                        script: "jq '.mse' artifacts/metrics.json",
                        returnStdout: true
                    ).trim()

                    env.CUR_R2 = sh(
                        script: "jq '.r2' artifacts/metrics.json",
                        returnStdout: true
                    ).trim()

                    echo "Current Metrics -> MSE=${env.CUR_MSE}, R2=${env.CUR_R2}"
                }
            }
        }

        // -------------------------------
        stage('Compare Accuracy') {
            steps {
                script {

                    boolean hasPrevious = true

                    // Try to fetch previous metrics.json
                    try {
                        copyArtifacts(
                        projectName: env.JOB_NAME,
                        selector: lastSuccessful(),
                        filter: 'artifacts/metrics.json',
                        target: 'previous',
                        optional: true
                        )
                    } catch (e) {
                        hasPrevious = false
                    }

                    if (!fileExists('previous/artifacts/metrics.json')) {
                        echo "No previous metrics found (first build). Approving deployment."
                        env.SHOULD_DEPLOY = "true"
                        return
                    }

                    def prevMSE = sh(
                        script: "jq '.mse' previous/artifacts/metrics.json",
                        returnStdout: true
                    ).trim()

                    def prevR2 = sh(
                        script: "jq '.r2' previous/artifacts/metrics.json",
                        returnStdout: true
                    ).trim()

                    echo "Previous Metrics -> MSE=${prevMSE}, R2=${prevR2}"

                    def betterR2 = sh(
                        script: "echo '${env.CUR_R2} > ${prevR2}' | bc -l",
                        returnStdout: true
                    ).trim()

                    def betterMSE = sh(
                        script: "echo '${env.CUR_MSE} < ${prevMSE}' | bc -l",
                        returnStdout: true
                    ).trim()

                    if (betterR2 == "1" && betterMSE == "1") {
                        env.SHOULD_DEPLOY = "true"
                        echo "Deployment approved (metrics improved)."
                    } else {
                        env.SHOULD_DEPLOY = "false"
                        echo "Deployment skipped (no improvement)."
                    }
                }
            }
        }

        // -------------------------------
        stage('Build Docker Image') {
            when {
                expression { env.SHOULD_DEPLOY == "true" }
            }
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'DOCKERHUB',
                        usernameVariable: 'DH_USER',
                        passwordVariable: 'DH_PASS'
                    )
                ]) {
                    sh '''
                        set -euxo pipefail
                        echo "${DH_PASS}" | docker login -u "${DH_USER}" --password-stdin

                        docker build \
                        -t ${DH_USER}/${DOCKER_IMAGE}:${BUILD_NUMBER} \
                        -t ${DH_USER}/${DOCKER_IMAGE}:latest \
                        .
                    '''
                }
            }
        }

        // -------------------------------
        stage('Push Docker Image') {
            when {
                expression { env.SHOULD_DEPLOY == "true" }
            }
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'DOCKERHUB',
                        usernameVariable: 'DH_USER',
                        passwordVariable: 'DH_PASS'
                    )
                ]) {
                    sh '''
                        set -euxo pipefail
                        docker push ${DH_USER}/${DOCKER_IMAGE}:${BUILD_NUMBER}
                        docker push ${DH_USER}/${DOCKER_IMAGE}:latest
                    '''
                }
            }
        }
    }

    // -------------------------------
    post {
        always {
            archiveArtifacts artifacts: 'artifacts/**, model/**',
                            fingerprint: true,
                            allowEmptyArchive: true

            echo "Artifacts archived."
            echo "Final Gate Decision: SHOULD_DEPLOY=${env.SHOULD_DEPLOY}"
        }
    }
}
