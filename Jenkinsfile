pipeline {
  agent any

  options { timestamps() }

  environment {
    VENV_DIR = '.venv'
    DOCKER_IMAGE = "wine_predict_2022bcs0168"
    SHOULD_DEPLOY = 'false'
    CUR_R2 = ''
    CUR_MSE = ''
    BASE_R2 = ''
    BASE_MSE = ''
  }

  stages {

    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Setup Python Virtual Environment') {
      steps {
        sh '''
          set -euxo pipefail
          python3 -m venv "${VENV_DIR}"
          . "${VENV_DIR}/bin/activate"
          pip install --upgrade pip
          pip install -r requirements.txt
          sudo apt-get update
          sudo apt-get install -y jq bc
        '''
      }
    }

    stage('Train Model') {
      steps {
        sh '''
          set -euxo pipefail
          . "${VENV_DIR}/bin/activate"
          python src/train.py
          test -f artifacts/metrics.json
        '''
      }
    }

    stage('Read Accuracy') {
      steps {
        script {
          env.CUR_MSE = sh(script: "jq '.mse' artifacts/metrics.json", returnStdout: true).trim()
          env.CUR_R2  = sh(script: "jq '.r2'  artifacts/metrics.json", returnStdout: true).trim()
          echo "Current metrics: MSE=${env.CUR_MSE}, R2=${env.CUR_R2}"
        }
      }
    }

    stage('Compare Accuracy') {
      steps {
        script {
          // Try to fetch baseline.json from last successful build.
          // If it doesn't exist (first run), initialize a permissive baseline.
          def haveBaseline = true
          try {
            copyArtifacts(
              projectName: env.JOB_NAME,
              selector: lastSuccessful(),
              filter: 'baseline.json',
              optional: true
            )
            if (!fileExists('baseline.json')) haveBaseline = false
          } catch (e) {
            haveBaseline = false
          }

          if (!haveBaseline) {
            echo "No baseline.json found from last successful build. Initializing baseline."
            // First run: set baseline so first successful model deploys (optional policy)
            writeFile file: 'baseline.json', text: '{"r2": -1e9, "mse": 1e18}\n'
          }

          env.BASE_R2  = sh(script: "jq '.r2'  baseline.json", returnStdout: true).trim()
          env.BASE_MSE = sh(script: "jq '.mse' baseline.json", returnStdout: true).trim()

          echo "Baseline metrics: BEST_R2=${env.BASE_R2}, BEST_MSE=${env.BASE_MSE}"

          def betterR2  = sh(script: "echo '${env.CUR_R2} > ${env.BASE_R2}' | bc -l", returnStdout: true).trim()
          def betterMSE = sh(script: "echo '${env.CUR_MSE} < ${env.BASE_MSE}' | bc -l", returnStdout: true).trim()

          if (betterR2 == '1' && betterMSE == '1') {
            env.SHOULD_DEPLOY = 'true'
            echo "✅ Deployment approved (metrics improved)."

            // Update baseline.json for next builds (persist via artifact)
            writeFile file: 'baseline.json',
              text: """{
  "r2": ${env.CUR_R2},
  "mse": ${env.CUR_MSE}
}
"""
          } else {
            env.SHOULD_DEPLOY = 'false'
            echo "⛔ Deployment skipped (no metric improvement)."
          }
        }
      }
    }

    stage('Build Docker Image (Conditional)') {
      when { expression { env.SHOULD_DEPLOY == 'true' } }
      steps {
        withCredentials([usernamePassword(credentialsId: 'DOCKERHUB', usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
          sh '''
            set -euxo pipefail
            echo "${DH_PASS}" | docker login -u "${DH_USER}" --password-stdin
            docker build -t "${DH_USER}/${DOCKER_IMAGE}:${BUILD_NUMBER}" -t "${DH_USER}/${DOCKER_IMAGE}:latest" .
          '''
        }
      }
    }

    stage('Push Docker Image (Conditional)') {
      when { expression { env.SHOULD_DEPLOY == 'true' } }
      steps {
        withCredentials([usernamePassword(credentialsId: 'DOCKERHUB', usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
          sh '''
            set -euxo pipefail
            docker push "${DH_USER}/${DOCKER_IMAGE}:${BUILD_NUMBER}"
            docker push "${DH_USER}/${DOCKER_IMAGE}:latest"
          '''
        }
      }
    }
  }

  post {
    always {
      // Lab requirement: always archive artifacts
      archiveArtifacts artifacts: 'artifacts/**, model/**, baseline.json',
                      fingerprint: true,
                      allowEmptyArchive: true
      echo "Archived artifacts/**, model/**, baseline.json"
    }
  }
}
