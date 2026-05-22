- Followed REQUIREMENTS.md: 
    ```
    git clone https://github.com/AIPI-561-Operationalizing-AI/Ops-AI-Student.git
    brew install git-lfs
    git lfs install
    git lfs pull
    cd Ops-AI-Student/
    git lfs pull 
    python3.11 -m venv venv
    source venv/bin/activate
    kubectl
    brew install --cask google-cloud-sdk\ngcloud init\ngcloud auth login
    source venv/bin/activate
    docker --version
    kubectl --version
    kubectl version --client
    gcloud config list 
    pip install -r backend/requirements.txt
    brew install libomp 
    pip install -r backend/requirements.txt 
    ```
- The lightgbm dependency install choked on openMP, used code to help diagnose and resolve: 
```
• I reproduced and fixed the install in ./venv.

  Root cause: the LightGBM failure was not primarily OpenMP. lightgbm==4.1.0 builds from source on this Python/macOS combo, and pip’s
  isolated build pulled CMake 4.3.2, which rejects LightGBM 4.1.0’s old cmake_minimum_required() policy.

  This worked:

  CMAKE_ARGS='-DCMAKE_POLICY_VERSION_MINIMUM=3.5' \
  CMAKE_PREFIX_PATH='/opt/homebrew/opt/libomp' \
  venv/bin/python -m pip install -r backend/requirements.txt

  Verification passed:

  No broken requirements found.
  lightgbm 4.1.0
  numpy 1.26.4
  scipy 1.17.1

  I also checked the built LightGBM library:

  /opt/homebrew/opt/llvm/lib/libomp.dylib

  So runtime OpenMP is available on this machine. One extra issue: importing the backend the way uvicorn likely will exposes a
  separate path problem in backend/data.py:14: it looks for data under /Users/jason/Local/school/561/Ops-AI-Student/data/
  processed/..., but this repo has week2/data/demand_enriched.parquet and week2/model/.... That is unrelated to pip/LightGBM, but it
  will matter when starting the API.
  ```
  - ❗️ Note the above uvicorn issue, which may manifest later
  - step 1: done 
  - step 2: done through web console since I don't know my account id 
  - step 3: done 
  - step 4: 👻
  - step 5: done 
    - amended to updload the text model instead based on new README
  - step 6: 
    ```
    gsutil cp week2/data/demand_enriched.parquet gs://ops-ai-jason-m-data/
    gsutil cp week2/model/demand_api_model.joblib gs://ops-ai-jason-m-data/
    gsutil cp week2/backend/zone_hour_avg_fare.parquet gs://ops-ai-jason-m-data/
    gsutil cp week2/backend/taxi_zones.geojson gs://ops-ai-jason-m-data/
    ```
    - lots of struggles uploading the first file, it's like reading from disk isn't working or pushing the file to the distant end isn't working. ended up manually uploading through the web console.     
 - step 7: done
 - step 8: `
    ```
    # Grant permissions (allow deployment to GKE, Artifact Registry, GCS)
    gcloud projects add-iam-policy-binding ops-ai-jason-m \
    --member=serviceAccount:github-actions@ops-ai-jason-m.iam.gserviceaccount.com \
    --role=roles/container.developer

    gcloud projects add-iam-policy-binding ops-ai-jason-m \
    --member=serviceAccount:github-actions@ops-ai-jason-m.iam.gserviceaccount.com \
    --role=roles/artifactregistry.writer

    gcloud projects add-iam-policy-binding ops-ai-jason-m \
    --member=serviceAccount:github-actions@ops-ai-jason-m.iam.gserviceaccount.com \
    --role=roles/storage.objectViewer

    # Also grant permissions to pull images from Artifact Registry
    gcloud projects add-iam-policy-binding ops-ai-jason-m \
    --member=serviceAccount:github-actions@ops-ai-jason-m.iam.gserviceaccount.com \
    --role=roles/artifactregistry.reader
    ```
  - step 9: 
    ```
    gcloud iam service-accounts keys create key.json \
    --iam-account=github-actions@ops-ai-jason-m.iam.gserviceaccount.com
    ```
  - PART 1: 
    - create k8s cluster
    ```
    gcloud container clusters create operationalizing-ai \
    --zone us-central1-a \
    --num-nodes 2 \
    --machine-type n1-standard-2 \
    --enable-autoscaling \
    --min-nodes 2 \
    --max-nodes 5 \
    --project ops-ai-jason-m
    ```
    - get credentials 
    ```
    gcloud container clusters get-credentials operationalizing-ai \
    --zone us-central1-a \
    --project ops-ai-jason-m
    ```
    - `kubectl get nodes` failed due to missing components 
      - `gcloud components install gke-gcloud-auth-plugin`
      - now works: 
      ```
      % kubectl get nodes
      NAME                                                 STATUS   ROLES    AGE     VERSION
      gke-operationalizing-ai-default-pool-eab0b4cc-f18j   Ready    <none>   8m26s   v1.35.3-gke.1389000
      gke-operationalizing-ai-default-pool-eab0b4cc-kjnz   Ready    <none>   8m27s   v1.35.3-gke.1389000
      ``1
  - PART 2:  
    - create secret
      ```  
      gcloud iam service-accounts keys create /tmp/gke-key.json \
        --iam-account=github-actions@ops-ai-jason-m.iam.gserviceaccount.com

      kubectl create secret docker-registry artifact-registry-secret \
        --docker-server=us-central1-docker.pkg.dev \
        --docker-username=_json_key \
        --docker-password="$(cat /tmp/gke-key.json)" \
        --docker-email=github-actions@ops-ai-jason-m.iam.gserviceaccount.com
      ```
    - verify: 
    ```
    % kubectl get secrets artifact-registry-secret
    NAME                       TYPE                             DATA   AGE
    artifact-registry-secret   kubernetes.io/dockerconfigjson   1      13s
    ```
    - removed key : `rm /tmp/gke-key.json`
    - NEW step 1b: create GCS service account secret 
      `kubectl create secret generic gcs-sa-key --from-file=key.json=key.json`
      - done and verified: 
      ```
      % kubectl get secrets gcs-sa-key
      NAME         TYPE     DATA   AGE
      gcs-sa-key   Opaque   1      7s
      ```
    - edit ConfigMap -> done
    - updated all entries 
  
  - PART 3: 
    - test docker build ... done
      - missing dependencies, need to be copied in - amended dockerfile 
    - deploy to k8s... success (3 pods because we have replicas = 3)
      ```
      % kubectl get pods
      NAME                          READY   STATUS     RESTARTS   AGE
      demand-api-7d665fc9cf-26stl   0/1     Init:0/1   0          44s
      demand-api-7d665fc9cf-vjdkm   0/1     Init:0/1   0          44s
      demand-api-7d665fc9cf-wkrwq   0/1     Init:0/1   0          44s
      ```
    - test curl request to external IP fails... 
      - inspect logs 
      ```
      % kubectl logs deployment/demand-api --tail=50
      Found 3 pods, using pod/demand-api-7d665fc9cf-26stl
      Error from server (BadRequest): container "demand-api" in pod "demand-api-7d665fc9cf-26stl" is waiting to start: trying and failing to pull image
      ```
        - hmm... where did we upload the image to the registry? we couldn't have if the build was failing. oh it's a CI step, which we haven't run yet and doesn't show up in the instructions until later. 
  - PART 4 
    - CI/CD won't be picked up in its current location -> copy to root of repo
    - build works, deploy doesn't 
      - our startup time wasn't conservative enough 
    - Serving works, but the model appears to fail to load: `[NYC Cab Analytics] Error loading LightGBM model: _Map_base::at`
      - vomits on load of txt model -- 
      - upgrade lightgbm package ftw
  - PART 5
    - `gcloud container clusters delete operationalizing-ai \
  --zone us-central1-a \
  --project ops-ai-jason-m`
    - `gcloud container clusters list --project ops-ai-jason-m`
    - `gcloud artifacts repositories delete docker-repo \
  --location=us-central1 \
  --project ops-ai-jason-m`
  - `gsutil ls gs://ops-ai-jason-m-data/`
